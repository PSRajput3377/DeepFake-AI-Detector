#!/usr/bin/env bash
# Full proper training pipeline for SDFVD (re-extract faces → train → copy to backend).
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="../backend/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Create backend venv first: cd ../backend && python3 -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

export TORCH_HOME="$(pwd)/.torch_cache"
mkdir -p .torch_cache checkpoints

echo "=== Step 1/4: Re-extract face crops with MTCNN (matches inference) ==="
"$PYTHON" preprocess.py --data ../SDFVD --out processed_faces --frames 30 --overwrite

echo "=== Step 2/4: Train (regularized for small dataset) ==="
"$PYTHON" train.py \
  --data processed_faces \
  --out checkpoints \
  --epochs 40 \
  --batch-size 4 \
  --sequence-length 12 \
  --freeze-backbone \
  --warmup-frozen 0 \
  --small-head \
  --clips-per-video 4 \
  --val-frac 0.25 \
  --metric f1_fake \
  --mixup-alpha 0.15 \
  --patience 15 \
  --num-workers 0

echo "=== Step 3/4: Evaluate on validation split ==="
"$PYTHON" evaluate.py --data processed_faces --weights checkpoints/best.pt --sequence-length 12

echo "=== Step 4/4: Copy weights for the API ==="
mkdir -p ../backend/models
cp checkpoints/best.pt ../backend/models/best.pt
echo ""
echo "Done. Start backend with real weights:"
echo "  cd ../backend"
echo "  echo 'DEEPFAKE_DEMO_MODE=0' > .env"
echo "  ../backend/.venv/bin/uvicorn app.main:app --reload --port 8000"
