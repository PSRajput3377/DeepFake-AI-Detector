"""PyTorch dataset for the pre-extracted face crops."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

import torch
from PIL import Image
from torch.utils.data import Dataset

LABEL_TO_INDEX = {"fake": 0, "real": 1}
INDEX_TO_LABEL = {v: k for k, v in LABEL_TO_INDEX.items()}


def _clip_has_frames(clip_dir: Path) -> bool:
    if not clip_dir.is_dir():
        return False
    return any(
        p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        for p in clip_dir.iterdir()
        if p.is_file()
    )


def discover_clips(root: Path) -> List[Tuple[Path, int]]:
    """Return [(clip_dir, label_index)] for every preprocessed clip on disk."""
    pairs: List[Tuple[Path, int]] = []
    for label, idx in LABEL_TO_INDEX.items():
        folder = root / label
        if not folder.is_dir():
            continue
        for clip_dir in sorted(folder.iterdir()):
            if _clip_has_frames(clip_dir):
                pairs.append((clip_dir, idx))
    return pairs


def discover_clips_many(roots: Iterable[Path]) -> List[Tuple[Path, int]]:
    """Merge clips from multiple preprocessed directories (same `real/` `fake/` layout each)."""
    merged: List[Tuple[Path, int]] = []
    for root in roots:
        merged.extend(discover_clips(Path(root)))
    return merged


class FaceClipsDataset(Dataset):
    """A dataset where every sample is a fixed-length clip of face crops."""

    def __init__(
        self,
        clips: List[Tuple[Path, int]],
        sequence_length: int = 20,
        transform: Optional[Callable] = None,
        train: bool = True,
        clips_per_video: int = 1,
        frame_drop_prob: float = 0.0,
    ):
        self.clips = clips
        self.sequence_length = sequence_length
        self.transform = transform
        self.train = train
        self.clips_per_video = max(1, clips_per_video)
        self.frame_drop_prob = frame_drop_prob if train else 0.0

    def __len__(self) -> int:
        return len(self.clips) * self.clips_per_video

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        clip_idx = idx // self.clips_per_video
        clip_dir, label = self.clips[clip_idx]
        if not clip_dir.is_dir():
            raise RuntimeError(f"clip directory missing (re-run preprocess): {clip_dir}")
        files = sorted(
            p for p in clip_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}
        )
        n = len(files)

        if n == 0:
            raise RuntimeError(f"empty clip dir: {clip_dir}")

        # Deterministic in val mode, random window in train mode.
        if self.train and n > self.sequence_length:
            start = random.randint(0, n - self.sequence_length)
            chosen = files[start : start + self.sequence_length]
        else:
            chosen = self._evenly_sampled(files, self.sequence_length)

        # Pad by repeating the last frame if the clip is too short.
        while len(chosen) < self.sequence_length:
            chosen.append(chosen[-1])

        # Temporal dropout: randomly replace some frames with a neighbour.
        if self.frame_drop_prob > 0 and len(chosen) > 2:
            for i in range(len(chosen)):
                if random.random() < self.frame_drop_prob:
                    j = max(0, min(len(chosen) - 1, i + random.choice([-1, 1])))
                    chosen[i] = chosen[j]

        frames = []
        for path in chosen:
            img = Image.open(path).convert("RGB")
            if self.transform is not None:
                img = self.transform(img)
            frames.append(img)

        clip = torch.stack(frames, dim=0)  # (T, 3, H, W)
        return clip, label

    @staticmethod
    def _evenly_sampled(files: List[Path], count: int) -> List[Path]:
        if not files:
            return []
        if len(files) <= count:
            return files
        step = len(files) / count
        return [files[min(len(files) - 1, int(round(i * step)))] for i in range(count)]
