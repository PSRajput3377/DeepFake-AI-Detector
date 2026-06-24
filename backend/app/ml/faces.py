"""Face detection with graceful fallbacks.

Detector preference order:

1. **MTCNN** (``facenet-pytorch``) — accurate, pure-PyTorch (no dlib).
   This is what the trainer uses to crop faces from the dataset, so
   matching it at inference time avoids train/test distribution drift.
2. **face_recognition** (dlib) — slow to install but very accurate.
3. **OpenCV Haar cascade** — bundled with opencv-python; lowest accuracy
   but always available.

All three return the legacy ``(top, right, bottom, left)`` tuple.
"""

from __future__ import annotations

from typing import Optional, Tuple

import cv2
import numpy as np


# ─── Capability detection (lazy) ──────────────────────────────────────
def _try_import_mtcnn() -> bool:
    try:
        from facenet_pytorch import MTCNN  # noqa: F401

        return True
    except Exception:
        return False


def _try_import_face_recognition() -> bool:
    try:
        import face_recognition  # noqa: F401

        return True
    except Exception:
        return False


HAS_MTCNN: bool = _try_import_mtcnn()
HAS_FACE_RECOGNITION: bool = _try_import_face_recognition()


# ─── MTCNN singleton ──────────────────────────────────────────────────
_MTCNN = None


def _mtcnn():
    global _MTCNN
    if _MTCNN is None and HAS_MTCNN:
        from facenet_pytorch import MTCNN
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _MTCNN = MTCNN(
            keep_all=False,
            device=device,
            post_process=False,
            select_largest=True,
        )
    return _MTCNN


# ─── Haar cascade singleton ───────────────────────────────────────────
_HAAR_CASCADE: Optional[cv2.CascadeClassifier] = None


def _haar_cascade() -> cv2.CascadeClassifier:
    global _HAAR_CASCADE
    if _HAAR_CASCADE is None:
        path = f"{cv2.data.haarcascades}haarcascade_frontalface_default.xml"
        _HAAR_CASCADE = cv2.CascadeClassifier(path)
    return _HAAR_CASCADE


# ─── Public API ───────────────────────────────────────────────────────
def detect_face_box(rgb_frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Return (top, right, bottom, left) for the largest face, or None."""
    if HAS_MTCNN:
        try:
            mtcnn = _mtcnn()
            if mtcnn is not None:
                boxes, _ = mtcnn.detect(rgb_frame)
                if boxes is not None and len(boxes) > 0:
                    x1, y1, x2, y2 = boxes[0]
                    return (int(y1), int(x2), int(y2), int(x1))
        except Exception:
            pass

    if HAS_FACE_RECOGNITION:
        try:
            import face_recognition

            faces = face_recognition.face_locations(rgb_frame)
            if faces:
                return max(faces, key=lambda f: (f[2] - f[0]) * (f[1] - f[3]))
        except Exception:
            pass

    cascade = _haar_cascade()
    gray = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)
    rects = cascade.detectMultiScale(
        gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60)
    )
    if len(rects) == 0:
        return None
    x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
    return (int(y), int(x + w), int(y + h), int(x))


def crop_face(
    rgb_frame: np.ndarray,
    box: Tuple[int, int, int, int],
    margin: float = 0.25,
) -> np.ndarray:
    """Square-crop a face with a fractional margin on every side."""
    h, w = rgb_frame.shape[:2]
    top, right, bottom, left = box
    bw = right - left
    bh = bottom - top
    side = max(bw, bh)
    cx = (left + right) // 2
    cy = (top + bottom) // 2
    half = int(side * (1 + 2 * margin) / 2)
    x1 = max(0, cx - half)
    y1 = max(0, cy - half)
    x2 = min(w, cx + half)
    y2 = min(h, cy + half)
    return rgb_frame[y1:y2, x1:x2]


def active_detector_name() -> str:
    if HAS_MTCNN:
        return "mtcnn"
    if HAS_FACE_RECOGNITION:
        return "dlib"
    return "haar"
