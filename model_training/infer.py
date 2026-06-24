"""Run a trained model on a single video file (sanity check).

Usage::

    python infer.py --weights checkpoints/best.pt --video path/to/clip.mp4
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

from _paths import DeepFakeDetector, ModelConfig, load_checkpoint  # noqa: F401
from app.ml.model import build_from_checkpoint
from preprocess import FaceCropper, sample_frames
from transforms import eval_transform


def main() -> int:
    parser = argparse.ArgumentParser(description="Single-video inference.")
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=20)
    parser.add_argument("--tta", type=int, default=1,
                        help="Number of randomly-shifted clips to ensemble.")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model, cfg, meta = build_from_checkpoint(str(args.weights), device=device)
    model.eval()
    print(f"[info] loaded {args.weights} (epoch={meta.get('epoch')}, "
          f"val_acc={meta.get('val_accuracy')}, "
          f"proj_dim={cfg.proj_dim}, lstm_hidden={cfg.lstm_hidden})")

    cropper = FaceCropper(cfg.image_size)
    transform = eval_transform(cfg.image_size)

    fake_probs = []
    for tta_idx in range(max(1, args.tta)):
        # Re-sample with a tiny offset for each TTA pass.
        n = args.frames + (tta_idx * 2)
        frames = sample_frames(args.video, n)[: args.frames]
        if not frames:
            print("[error] could not read any frames from", args.video)
            return 1

        tensors = []
        for frame in frames:
            crop = cropper.crop(frame)
            if crop is None:
                crop = cv2.resize(frame, (cfg.image_size, cfg.image_size))
            tensors.append(transform(Image.fromarray(crop)))
        clip = torch.stack(tensors, dim=0).unsqueeze(0).to(device)

        with torch.no_grad():
            logits, per_frame = model(clip, return_per_frame=True)
            probs = torch.softmax(logits, dim=1)[0]
        fake_probs.append(float(probs[0].item()))
        if tta_idx == 0:
            print("[per-frame fake probs]", np.round(per_frame[0].cpu().numpy(), 3).tolist())

    fake_prob = float(np.mean(fake_probs))
    real_prob = 1 - fake_prob
    label = "FAKE" if fake_prob >= real_prob else "REAL"
    print()
    print(f"verdict      : {label}")
    print(f"fake prob    : {fake_prob:.3f}")
    print(f"real prob    : {real_prob:.3f}")
    print(f"confidence   : {max(fake_prob, real_prob):.3f}")
    if args.tta > 1:
        print(f"tta passes   : {args.tta}  (stddev={np.std(fake_probs):.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
