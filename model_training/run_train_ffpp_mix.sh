#!/usr/bin/env bash
# Merge SDFVD + FaceForensics++ into one face-crop folder, then train.
#
# 1. Request FaceForensics++ access: https://github.com/ondyari/FaceForensics
# 2. Unpack so $FFPP_ROOT contains original_sequences/ and manipulated_sequences/
# 3. Run:
#      export FFPP_ROOT="/path/to/dataset/root"
#      ./run_train_ffpp_mix.sh
#
# FF++ preprocessing is large and slow on CPU — start with a subset by copying fewer
# videos into a smaller tree if needed.

set -euo pipefail
cd "$(dirname "$0")"

PYTHON="../backend/.venv/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  echo "Create backend venv first: cd ../backend && python3 -m venv .venv && pip install -r requirements.txt"
  exit 1
fi

if [[ -z "${FFPP_ROOT:-}" ]]; then
  echo "Set FFPP_ROOT to the FaceForensics++ root (folders original_sequences & manipulated_sequences)."
  exit 1
fi

MERGED_DIR="${MERGED_DIR:-processed_mixed_ffpp}"

export TORCH_HOME="$(pwd)/.torch_cache"
mkdir -p .torch_cache checkpoints

echo "=== 1/3: Face crops from SDFVD → ${MERGED_DIR} ==="
"$PYTHON" preprocess.py --data ../SDFVD --out "$MERGED_DIR" --frames 30

echo "=== 2/3: Append FaceForensics++ crops (--unique-clip-ids avoids name clashes) ==="
"$PYTHON" preprocess.py --data "$FFPP_ROOT" --layout ffplusplus \
  --out "$MERGED_DIR" --frames 30 --unique-clip-ids

echo "=== 3/3: Train on merged dataset ==="
"$PYTHON" train.py \
  --data "$MERGED_DIR" \
  --out checkpoints \
  --epochs 40 \
  --batch-size 4 \
  --sequence-length 16 \
  --clips-per-video 4 \
  --val-frac 0.2 \
  --metric f1_fake \
  --mixup-alpha 0.1 \
  --patience 20 \
  --num-workers 0 \
  --warmup-frozen 3

echo "=== Copy checkpoint for API ==="
mkdir -p ../backend/models
cp checkpoints/best.pt ../backend/models/best.pt
echo "Done. Use DEEPFAKE_DEMO_MODE=0 (and optionally DEEPFAKE_USE_PRETRAINED_HF=0) in backend."
