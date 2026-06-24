"""HuggingFace pretrained deepfake-image classifier predictor.

This is the right choice when you need predictions on **arbitrary
in-the-wild videos** rather than just the SDFVD distribution. The
pretrained models on HuggingFace have been fine-tuned on much larger and
more diverse deepfake datasets (FaceForensics++, DFDC, custom mixes), so
they generalize far better than a model trained on 49 SDFVD videos.

Default model: ``prithivMLmods/Deep-Fake-Detector-Model`` — a ViT-based
classifier with two output classes ("Real" / "Fake").

Other good drop-in alternatives:
* ``prithivMLmods/Deep-Fake-Detector-v2-Model``
* ``dima806/deepfake_vs_real_image_detection``

Set ``DEEPFAKE_HF_MODEL_ID`` to switch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
import numpy as np
from PIL import Image

from ..config import settings
from .faces import crop_face, detect_face_box


@dataclass
class _Result:
    label: str
    confidence: float
    real_prob: float
    fake_prob: float
    per_frame_fake_prob: List[float]


def _try_import_hf() -> bool:
    try:
        import transformers  # noqa: F401

        return True
    except Exception:
        return False


HAS_TRANSFORMERS: bool = _try_import_hf()


class PretrainedHFPredictor:
    """Aggregates per-frame fake probability from a pretrained HF classifier."""

    def __init__(self, model_id: str | None = None):
        import torch
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_id = model_id or settings.hf_model_id

        cache = str(settings.hf_cache_dir)
        Path(cache).mkdir(parents=True, exist_ok=True)
        self.processor = AutoImageProcessor.from_pretrained(self.model_id, cache_dir=cache)
        self.model = AutoModelForImageClassification.from_pretrained(
            self.model_id, cache_dir=cache
        ).to(self.device)
        self.model.eval()

        # The two HF deepfake classifiers we recommend label classes as
        # {0: "Real", 1: "Fake"} or {0: "Fake", 1: "Real"} — figure it out
        # from id2label rather than hardcoding.
        id2label = {int(k): str(v) for k, v in self.model.config.id2label.items()}
        self.fake_idx = next(
            (i for i, lbl in id2label.items() if "fake" in lbl.lower()), 1
        )
        self.real_idx = next(
            (i for i, lbl in id2label.items() if "real" in lbl.lower()), 0
        )

        short = self.model_id.split("/")[-1]
        self.name = f"HF Pretrained · {short}"

    def predict(self, video_path: str | Path, frames: List[np.ndarray]) -> _Result:
        if not frames:
            return _Result("REAL", 0.5, 0.5, 0.5, [])

        per_frame_fake: List[float] = []
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            box = detect_face_box(rgb)
            crop = crop_face(rgb, box, margin=0.25) if box is not None else rgb
            if crop.size == 0:
                crop = rgb

            pil = Image.fromarray(crop)
            inputs = self.processor(images=pil, return_tensors="pt").to(self.device)
            with self.torch.no_grad():
                logits = self.model(**inputs).logits
                probs = self.torch.softmax(logits, dim=-1)[0]

            per_frame_fake.append(float(probs[self.fake_idx].item()))

        avg_fake = float(np.mean(per_frame_fake))
        avg_real = 1.0 - avg_fake
        label = "FAKE" if avg_fake >= avg_real else "REAL"
        return _Result(
            label=label,
            confidence=max(avg_fake, avg_real),
            real_prob=avg_real,
            fake_prob=avg_fake,
            per_frame_fake_prob=per_frame_fake,
        )
