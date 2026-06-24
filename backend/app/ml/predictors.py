"""Predictors used by the API.

* ``DemoPredictor`` — model-free, deterministic, signal-based. Always
  available so the API works end-to-end without trained weights.
* ``RealPredictor`` — wraps the trained ResNeXt + LSTM + MobileViT model
  when a matching ``.pt`` checkpoint is found in ``models/``.
* ``PretrainedHFPredictor`` (in ``hf_predictor.py``) — wraps a
  HuggingFace pretrained deepfake-image classifier. Use this when you
  need predictions on **arbitrary in-the-wild videos** instead of just
  the SDFVD distribution.

The factory ``get_predictor()`` picks the right one based on
``settings.use_pretrained_hf``, ``settings.demo_mode``, and what's on
disk.
"""

from __future__ import annotations

import glob
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from ..config import settings
from .faces import crop_face, detect_face_box


@dataclass
class PredictionResult:
    label: str
    confidence: float
    real_prob: float
    fake_prob: float
    per_frame_fake_prob: List[float]


def _try_import_torch() -> bool:
    try:
        import torch  # noqa: F401
        from torch import nn  # noqa: F401
        from torchvision import models  # noqa: F401

        return True
    except Exception:
        return False


HAS_TORCH: bool = _try_import_torch()


# ─── Demo mode (always available) ────────────────────────────────────
class DemoPredictor:
    """Deterministic, model-free predictor used when no weights are present."""

    name = "DemoPredictor (heuristic)"

    @staticmethod
    def _file_seed(video_path: str | Path) -> int:
        h = hashlib.sha256()
        bytes_read = 0
        with open(video_path, "rb") as f:
            while bytes_read < (4 << 20):
                chunk = f.read(1 << 20)
                if not chunk:
                    break
                h.update(chunk)
                bytes_read += len(chunk)
        return int.from_bytes(h.digest()[:8], "big")

    @staticmethod
    def _frame_score(frame_bgr: np.ndarray) -> float:
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        blur = cv2.Laplacian(gray, cv2.CV_64F).var()
        hist = cv2.calcHist([gray], [0], None, [32], [0, 256]).flatten()
        hist = hist / (hist.sum() + 1e-9)
        entropy = -np.sum(hist * np.log2(hist + 1e-9))
        blur_norm = math.tanh(50.0 / (blur + 1.0))
        entropy_norm = max(0.0, min(1.0, (5.5 - entropy) / 5.5))
        return float(0.6 * blur_norm + 0.4 * entropy_norm)

    def predict(
        self, video_path: str | Path, frames: List[np.ndarray]
    ) -> PredictionResult:
        seed = self._file_seed(video_path)
        rng = np.random.default_rng(seed)
        base = (seed % 1000) / 1000.0
        heuristic = (
            float(np.mean([self._frame_score(f) for f in frames])) if frames else 0.5
        )
        fake_prob = float(np.clip(0.55 * base + 0.45 * heuristic, 0.02, 0.98))
        real_prob = 1.0 - fake_prob
        n = max(1, len(frames))
        jitter = rng.normal(0, 0.06, size=n)
        smoothed = np.convolve(jitter, np.ones(3) / 3, mode="same")
        per_frame = np.clip(fake_prob + smoothed, 0.02, 0.98).tolist()
        label = "FAKE" if fake_prob >= 0.5 else "REAL"
        return PredictionResult(label, max(real_prob, fake_prob), real_prob, fake_prob, per_frame)


# ─── Real predictor (requires PyTorch + a .pt checkpoint) ─────────────
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class RealPredictor:
    """Wraps the ResNeXt + LSTM + MobileViT model with training preprocessing."""

    def __init__(self, model_path: str | Path):
        import torch
        from torchvision import transforms

        from .model import build_from_checkpoint

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Build the model with the architecture that was actually saved in the
        # checkpoint — this is what makes `--small-head` runs load correctly.
        self.model, self.cfg, self.meta = build_from_checkpoint(
            str(model_path), device=self.device
        )
        self.model.eval()

        self.transforms = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize((self.cfg.image_size, self.cfg.image_size)),
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ]
        )
        acc = self.meta.get("val_accuracy")
        suffix = f" · val acc {acc:.1%}" if isinstance(acc, (float, int)) else ""
        self.name = f"ResNeXt-50 + LSTM + MobileViT{suffix}"

    def _build_clip(self, frames: List[np.ndarray]) -> Optional["torch.Tensor"]:
        torch = self.torch
        tensors = []
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            box = detect_face_box(rgb)
            crop = crop_face(rgb, box, margin=0.25) if box is not None else rgb
            if crop.size == 0:
                crop = rgb
            tensors.append(self.transforms(crop))
        if not tensors:
            return None
        return torch.stack(tensors).unsqueeze(0).to(self.device)  # (1, T, 3, H, W)

    def predict(
        self, video_path: str | Path, frames: List[np.ndarray]
    ) -> PredictionResult:
        x = self._build_clip(frames)
        if x is None:
            return PredictionResult("REAL", 0.5, 0.5, 0.5, [])

        with self.torch.no_grad():
            logits, per_frame_fake = self.model(x, return_per_frame=True)
            probs = self.torch.softmax(logits, dim=1)[0]

        # Class index 0 = FAKE, 1 = REAL (matches the trainer's labelling).
        fake_prob = float(probs[0].item())
        real_prob = float(probs[1].item())
        label = "FAKE" if fake_prob >= real_prob else "REAL"
        return PredictionResult(
            label=label,
            confidence=max(real_prob, fake_prob),
            real_prob=real_prob,
            fake_prob=fake_prob,
            per_frame_fake_prob=per_frame_fake[0].cpu().tolist(),
        )


def find_best_model() -> Optional[Path]:
    """Pick the highest-accuracy ``.pt`` we can find under ``models/``.

    Convention: ``best.pt`` (from the trainer) takes precedence; otherwise we
    fall back to alphabetical order.
    """
    if not HAS_TORCH:
        return None
    explicit = settings.models_dir / "best.pt"
    if explicit.exists():
        return explicit
    candidates = sorted(glob.glob(str(settings.models_dir / "*.pt")))
    if not candidates:
        return None
    return Path(candidates[-1])


_PREDICTOR_CACHE: Dict[str, object] = {}


def get_predictor(_sequence_length: int = 0):
    """Factory used by the FastAPI route.

    Resolution order:

    1. ``DEEPFAKE_USE_PRETRAINED_HF=1`` → :class:`PretrainedHFPredictor`
       (works on **any** video, downloads ~300 MB on first use).
    2. ``DEEPFAKE_DEMO_MODE=1`` (default) → :class:`DemoPredictor`.
    3. Otherwise: trained ``best.pt`` if found, else fall back to demo.

    The ``sequence_length`` argument is accepted for backwards compatibility.
    """
    if settings.use_pretrained_hf:
        from .hf_predictor import HAS_TRANSFORMERS, PretrainedHFPredictor

        if not HAS_TRANSFORMERS:
            print(
                "[warn] DEEPFAKE_USE_PRETRAINED_HF=1 but `transformers` is not "
                "installed. Run `pip install transformers safetensors`. "
                "Falling back to DemoPredictor."
            )
            return DemoPredictor()
        key = f"hf::{settings.hf_model_id}"
        if key not in _PREDICTOR_CACHE:
            _PREDICTOR_CACHE[key] = PretrainedHFPredictor(settings.hf_model_id)
        return _PREDICTOR_CACHE[key]

    if settings.demo_mode:
        return DemoPredictor()

    model_path = find_best_model()
    if not model_path:
        return DemoPredictor()
    key = str(model_path)
    if key not in _PREDICTOR_CACHE:
        _PREDICTOR_CACHE[key] = RealPredictor(model_path)
    return _PREDICTOR_CACHE[key]
