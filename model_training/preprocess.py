"""Extract face crops from every video into a fixed-size dataset.

Why this exists: re-running face detection every training step is *slow*,
and it tightly couples the data pipeline to dlib. We instead detect once,
write 224×224 RGB JPEGs to disk, and let training read them with vanilla
PIL + torchvision transforms.

Output layout::

    <out>/
      ├─ real/<video_id>/000.jpg ... 029.jpg
      └─ fake/<video_id>/000.jpg ... 029.jpg

``--layout ffplusplus`` follows the FaceForensics++ directory convention
(``original_sequences/**`` → real, ``manipulated_sequences/**`` → fake).

Usage::

    python preprocess.py --data ../SDFVD --out processed_faces
    python preprocess.py --data ~/FaceForensics --layout ffplusplus --out processed_ffpp \\
        --unique-clip-ids
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

# We keep MTCNN optional so users without facenet-pytorch can still run a
# Haar-cascade preprocessing pass (lower quality but always works).
try:
    import torch
    from facenet_pytorch import MTCNN

    HAS_MTCNN = True
except Exception:  # pragma: no cover
    HAS_MTCNN = False


# ─── Defaults ─────────────────────────────────────────────────────────
DEFAULT_FRAMES_PER_VIDEO = 30
DEFAULT_IMAGE_SIZE = 224
SUPPORTED_EXT = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".gif", ".mpeg", ".mpg"}

# SDFVD's two folders → our binary class labels.
SDFVD_CLASS_FOLDERS = {
    "videos_real": "real",
    "videos_fake": "fake",
}


# ─── Face detection ───────────────────────────────────────────────────
class FaceCropper:
    """Wraps MTCNN with a Haar-cascade fallback."""

    def __init__(self, image_size: int, device: str | None = None):
        self.image_size = image_size
        if device:
            self.device = device
        elif HAS_MTCNN and torch.cuda.is_available():
            self.device = "cuda"
        elif (
            HAS_MTCNN
            and getattr(torch.backends, "mps", None) is not None
            and torch.backends.mps.is_available()
        ):
            self.device = "mps"
        else:
            self.device = "cpu"

        self.mtcnn = None
        if HAS_MTCNN:
            self.mtcnn = MTCNN(
                keep_all=False,
                device=self.device,
                post_process=False,
                select_largest=True,
                margin=20,
            )

        haar_path = f"{cv2.data.haarcascades}haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(haar_path)

    def crop(self, rgb_frame: np.ndarray) -> np.ndarray | None:
        """Return a 224×224 RGB face crop, or None if no face is found."""
        h, w = rgb_frame.shape[:2]
        box = self._detect(rgb_frame)
        if box is None:
            return None
        x1, y1, x2, y2 = box
        bw = x2 - x1
        bh = y2 - y1
        side = max(bw, bh)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        margin = 0.25
        half = int(side * (1 + 2 * margin) / 2)
        x1 = max(0, cx - half)
        y1 = max(0, cy - half)
        x2 = min(w, cx + half)
        y2 = min(h, cy + half)
        crop = rgb_frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        return cv2.resize(crop, (self.image_size, self.image_size), interpolation=cv2.INTER_AREA)

    # ---- private --------------------------------------------------------
    def _detect(self, rgb_frame: np.ndarray) -> Tuple[int, int, int, int] | None:
        if self.mtcnn is not None:
            try:
                boxes, _ = self.mtcnn.detect(rgb_frame)
                if boxes is not None and len(boxes) > 0:
                    x1, y1, x2, y2 = boxes[0]
                    return int(x1), int(y1), int(x2), int(y2)
            except Exception:
                pass

        gray = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)
        rects = self.cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60)
        )
        if len(rects) == 0:
            return None
        x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
        return int(x), int(y), int(x + w), int(y + h)


# ─── Video helpers ────────────────────────────────────────────────────
def evenly_spaced_indices(total: int, count: int) -> List[int]:
    if total <= 0 or count <= 0:
        return []
    if total <= count:
        return list(range(total))
    step = total / count
    return [min(total - 1, int(round(i * step))) for i in range(count)]


def sample_frames(video_path: Path, count: int) -> List[np.ndarray]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    indices = set(evenly_spaced_indices(total, count)) if total else None
    frames: List[np.ndarray] = []
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if indices is None or idx in indices:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += 1
        if indices is not None and len(frames) >= count:
            break
    cap.release()
    return frames[:count]


def discover_videos_sdfvd_flat(data_dir: Path) -> List[Tuple[Path, str]]:
    """SDFVD `videos_*` dirs or `<root>/{real,fake}/*.mp4` (single level)."""
    pairs: List[Tuple[Path, str]] = []
    for sub, label in SDFVD_CLASS_FOLDERS.items():
        folder = data_dir / sub
        if not folder.is_dir():
            continue
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in SUPPORTED_EXT:
                pairs.append((f, label))

    # Generic fallback: if the user already organized as <root>/{real,fake}/
    if not pairs:
        for label in ("real", "fake"):
            folder = data_dir / label
            if not folder.is_dir():
                continue
            for f in sorted(folder.iterdir()):
                if f.suffix.lower() in SUPPORTED_EXT:
                    pairs.append((f, label))
    return pairs


def discover_videos_ffplusplus(data_dir: Path) -> List[Tuple[Path, str]]:
    """FaceForensics++ unpacked layout under one root folder.

    Expects::
        original_sequences/**/*.mp4
        manipulated_sequences/**/*.mp4

    Matches all common codecs / manipulations recursively (Deepfakes,
    Face2Face, FaceSwap, NeuralTextures, ...).
    """
    pairs: List[Tuple[Path, str]] = []
    orig = data_dir / "original_sequences"
    manip = data_dir / "manipulated_sequences"

    def walk_with_label(root: Path, label: str) -> None:
        if not root.is_dir():
            return
        for f in sorted(root.rglob("*")):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXT:
                pairs.append((f, label))

    walk_with_label(orig, "real")
    walk_with_label(manip, "fake")
    return pairs


def discover_videos(data_dir: Path, layout: str) -> List[Tuple[Path, str]]:
    """Return [(video_path, label)] for the dataset at ``data_dir``."""
    lay = layout.lower().strip()
    if lay == "auto":
        pairs = discover_videos_sdfvd_flat(data_dir)
        if pairs:
            return pairs
        return discover_videos_ffplusplus(data_dir)
    if lay in ("sdfvd", "flat"):
        return discover_videos_sdfvd_flat(data_dir)
    if lay == "ffplusplus":
        return discover_videos_ffplusplus(data_dir)
    raise ValueError(f"unsupported layout {layout!r}")


def clip_output_stem(video_path: Path, unique_clip_ids: bool) -> str:
    base = video_path.stem
    if not unique_clip_ids:
        return base
    digest = hashlib.md5(str(video_path.resolve()).encode()).hexdigest()[:8]
    return f"{base}_{digest}"


# ─── Main ─────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract face crops from videos for fast training."
    )
    parser.add_argument("--data", type=Path, required=True, help="Dataset root.")
    parser.add_argument(
        "--layout",
        choices=("auto", "sdfvd", "ffplusplus"),
        default="auto",
        help="auto: SDFVD or real/fake/ first, else FF++ original/manipulated trees.",
    )
    parser.add_argument("--out", type=Path, default=Path("processed_faces"),
                        help="Where to write face crops.")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES_PER_VIDEO,
                        help="Frames sampled per video.")
    parser.add_argument("--size", type=int, default=DEFAULT_IMAGE_SIZE,
                        help="Output crop size (square).")
    parser.add_argument("--min-faces", type=int, default=8,
                        help="Skip videos with fewer than this many usable faces.")
    parser.add_argument("--overwrite", action="store_true",
                        help="Re-extract videos even if their folder already exists.")
    parser.add_argument(
        "--unique-clip-ids",
        action="store_true",
        help="Append a short hash to each clip folder name (avoids collisions when mixing sources).",
    )
    args = parser.parse_args()

    if not args.data.is_dir():
        print(f"[error] data dir not found: {args.data}", file=sys.stderr)
        return 1

    pairs = discover_videos(args.data, args.layout)
    if not pairs:
        hint = ""
        if args.layout == "ffplusplus":
            hint = " (expected original_sequences/ and manipulated_sequences/)"
        elif args.layout == "auto":
            hint = " (try --layout ffplusplus if this is FaceForensics++)"
        print(f"[error] no videos found under {args.data}{hint}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    cropper = FaceCropper(args.size)
    print(
        f"[info] preprocessing {len(pairs)} videos with "
        f"{'MTCNN' if cropper.mtcnn is not None else 'Haar cascade'} "
        f"({args.frames} frames each) → {args.out}"
    )

    written = 0
    skipped = 0
    for video_path, label in tqdm(pairs, desc="videos"):
        stem = clip_output_stem(video_path, args.unique_clip_ids)
        out_dir = args.out / label / stem
        if out_dir.exists() and not args.overwrite and any(out_dir.iterdir()):
            continue
        out_dir.mkdir(parents=True, exist_ok=True)

        frames = sample_frames(video_path, args.frames)
        if not frames:
            skipped += 1
            continue

        n_ok = 0
        for i, frame in enumerate(frames):
            crop = cropper.crop(frame)
            if crop is None:
                continue
            Image.fromarray(crop).save(out_dir / f"{i:03d}.jpg", quality=92)
            n_ok += 1

        if n_ok < args.min_faces:
            # Not enough faces for a meaningful clip — drop the folder.
            for f in out_dir.iterdir():
                f.unlink()
            out_dir.rmdir()
            skipped += 1
        else:
            written += 1

    print(
        f"[done] wrote {written} videos · skipped {skipped} "
        f"(insufficient or unreadable) · output → {args.out.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
