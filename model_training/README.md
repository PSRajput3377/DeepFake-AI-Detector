# Model Training

Train the **ResNeXt-50 + LSTM + MobileViT** deepfake detector.

The same model class is shared with the FastAPI backend (`backend/app/ml/model.py`),
so any checkpoint produced here drops straight into `backend/models/best.pt`
and the inference API picks it up automatically.

## Setup

```bash
cd model_training
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

> If `facenet-pytorch` fails to install on your machine, you can comment it
> out in `requirements.txt` — the preprocessor falls back to OpenCV's Haar
> cascade. Quality is lower but the pipeline still runs.

## End-to-end recipe (SDFVD)

```bash
# 1. extract face crops once  (~3 min on CPU for 106 videos)
python preprocess.py --data ../SDFVD --out processed_faces

# 2a. SMALL-DATASET recipe (recommended for SDFVD's 98 videos)
#     Fully frozen ResNeXt + tiny LSTM+MobileViT head + multi-clip sampling.
#     ~30-60 min total on CPU; reaches ~70-80% val acc on SDFVD.
python train.py --data processed_faces \
    --epochs 25 --batch-size 4 --sequence-length 12 \
    --freeze-backbone --warmup-frozen 0 \
    --small-head --clips-per-video 8 --patience 12

# 2b. SLOW / high-quality recipe — 5+ hours on CPU
#     unfreezes layer4 after warmup; only do this if you have a GPU
python train.py --data processed_faces --epochs 30 --batch-size 4

# 3. evaluate
python evaluate.py --data processed_faces --weights checkpoints/best.pt --sequence-length 12

# 4. quick single-video sanity check
python infer.py --weights checkpoints/best.pt --video ../SDFVD/videos_fake/vs1.mp4 --frames 12

# 5. ship the trained weights to the backend
mkdir -p ../backend/models
cp checkpoints/best.pt ../backend/models/best.pt
DEEPFAKE_DEMO_MODE=0 uvicorn app.main:app --reload --port 8000  # in backend/
```

### Speed knobs

| Knob                       | Effect                                                                 |
| -------------------------- | ---------------------------------------------------------------------- |
| `--freeze-backbone`        | Keeps ResNeXt frozen — **5-10× faster on CPU** (no backward through it).|
| `--small-head`             | Shrinks the trainable head from 6.8M → 495K params — **prevents overfitting on small datasets**. |
| `--clips-per-video N`      | Samples N random windows per video per epoch — multiplies effective data N×. |
| `--sequence-length 12`     | 12 frames per clip instead of 20 — **~1.7× faster**.                    |
| `--warmup-frozen 0`        | Skip the 3-epoch frozen warmup since backbone stays frozen anyway.     |
| `--device mps`             | Force Apple Silicon GPU. Auto-detected, but you can override.          |
| `--num-workers 0`          | Helps if DataLoader parallelism is causing macOS issues.               |

The trainer auto-detects CUDA → MPS → CPU. On a modern M-series Mac with
`--freeze-backbone`, expect **~30-60 sec per epoch**.

## What each script does

### `preprocess.py`
Walks every video in the dataset, samples `--frames` evenly-spaced frames,
runs **MTCNN** (or Haar) face detection, square-crops + resizes to 224×224
and writes JPEGs to `processed_faces/{real,fake}/<video_id>/000.jpg`.
This is the single slowest step — running it once means training reads
fast PIL images instead of doing detection on every batch.

| Flag           | Default | Notes                                             |
| -------------- | ------- | ------------------------------------------------- |
| `--data`       | —       | Dataset root (SDFVD-style or `<root>/{real,fake}/`) |
| `--out`        | `processed_faces` | Output dir                                |
| `--frames`     | `30`    | Frames per video                                  |
| `--size`       | `224`   | Output crop size                                  |
| `--min-faces`  | `8`     | Skip videos with fewer usable faces               |
| `--overwrite`  | off     | Re-extract videos that already exist              |

### `train.py`
The actual training loop. Key design choices:

- **Frozen warm-up**: ResNeXt-50 is fully frozen for the first 3 epochs so
  the new head (LSTM + MobileViT + classifier) gets to settle before
  bigger gradients flow into the backbone.
- **Layer4 fine-tune**: after the warmup, only ResNeXt's last conv block is
  unfrozen — keeps the early ImageNet features intact.
- **Discriminative LR**: the head trains at `3e-4`, the backbone at `3e-5`.
- **AdamW + cosine schedule with warmup**, gradient clipping at 1.0.
- **Class-weighted CE loss** (handles imbalance) with `label_smoothing=0.05`.
- **Stratified split on the *video* level** — same video never appears in
  both train and val.
- **Early stopping** on val accuracy with `--patience` (default 8 epochs).
- **AMP / GradScaler** automatically when CUDA is available.
- Saves `best.pt`, `latest.pt` and `history.json` in `--out`.

| Flag                   | Default | Notes |
| ---------------------- | ------- | ----- |
| `--epochs`             | `30`    | |
| `--batch-size`         | `4`     | Each clip has T=20 frames, so memory ≈ 4×20×3×224×224 |
| `--sequence-length`    | `20`    | T |
| `--clips-per-video`    | `2`     | Random window samples / video / epoch (data multiplier) |
| `--lr-head`            | `3e-4`  | |
| `--lr-backbone`        | `3e-5`  | |
| `--warmup-frozen`      | `3`     | Epochs with backbone frozen |
| `--patience`           | `8`     | Early stopping |
| `--num-workers`        | `2`     | DataLoader workers |
| `--no-pretrained`      | off     | NOT recommended |

### `evaluate.py`
Re-runs the val split with the chosen checkpoint and writes:

- `eval_results/metrics.json` (accuracy, precision, recall, F1, ROC-AUC for
  the fake class, support, confusion matrix)
- `eval_results/confusion_matrix.png`

### `infer.py`
Single-video sanity check with optional Test-Time Augmentation
(`--tta N` averages over N differently-sampled clips).

## Realistic expectations

SDFVD is **tiny** (53 + 53 = 106 videos). Even a perfectly tuned hybrid
model will plateau around **85–92% val accuracy** on this dataset. To
push beyond that you'll want:

- **FaceForensics++** (1000 manipulated videos × 4 methods)
- **Celeb-DF v2** (5,639 deepfake videos)
- **DFDC** (~100k videos)

The exact same scripts work for any folder structure of the form
`<root>/{real,fake}/<video>.mp4` — just point `--data` at the new dataset
and (optionally) increase `--frames`, `--epochs` and `--batch-size`.

## Where the model class lives

The trainer imports `DeepFakeDetector` from `backend/app/ml/model.py`. The
backend imports the same class. There is one source of truth, so there's
no risk of an architecture mismatch when loading a trained `.pt`.
