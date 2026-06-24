#!/usr/bin/env bash
# ~10–15 min on Apple Silicon (MPS). Good enough for demos + SDFVD in-distribution.
set -euo pipefail
cd "$(dirname "$0")"
PYTHON="../backend/.venv/bin/python"
export TORCH_HOME="$(pwd)/.torch_cache"
mkdir -p .torch_cache checkpoints

"$PYTHON" train.py \
  --data processed_faces \
  --out checkpoints \
  --epochs 12 \
  --batch-size 8 \
  --sequence-length 8 \
  --freeze-backbone \
  --warmup-frozen 0 \
  --small-head \
  --clips-per-video 2 \
  --val-frac 0.2 \
  --metric f1_fake \
  --mixup-alpha 0 \
  --patience 6 \
  --num-workers 0 \
  --no-strong-aug

mkdir -p ../backend/models
cp checkpoints/best.pt ../backend/models/best.pt
echo "Copied → ../backend/models/best.pt (restart backend with DEEPFAKE_DEMO_MODE=0)"
