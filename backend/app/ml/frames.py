"""Video frame extraction helpers built on OpenCV."""

from __future__ import annotations

from pathlib import Path
from typing import List

import cv2
import numpy as np


def evenly_spaced_indices(total: int, count: int) -> List[int]:
    if total <= 0 or count <= 0:
        return []
    if total <= count:
        return list(range(total))
    step = total / count
    return [min(total - 1, int(round(i * step))) for i in range(count)]


def extract_frames(video_path: str | Path, count: int) -> List[np.ndarray]:
    """Extract at most `count` evenly-spaced BGR frames from a video.

    Falls back to sequential reading when the container does not advertise
    a frame count (e.g. some web-streamed mp4s).
    """
    path = str(video_path)
    cap = cv2.VideoCapture(path)
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
            frames.append(frame)
        idx += 1
        if indices is not None and len(frames) >= count:
            break
    cap.release()

    if not frames and total == 0:
        cap = cv2.VideoCapture(path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            if len(frames) >= count:
                break
        cap.release()

    return frames[:count]
