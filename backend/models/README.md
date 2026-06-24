# Trained model checkpoints

Drop your trained `.pt` files into this folder.

The backend automatically picks them up:

1. If `best.pt` exists, it's loaded.
2. Otherwise the alphabetically last `*.pt` is loaded.
3. If no `.pt` exists, the API silently falls back to `DemoPredictor`.

## Producing a checkpoint

```bash
cd ../../model_training
python preprocess.py --data ../SDFVD --out processed_faces
python train.py --data processed_faces --epochs 30 --batch-size 4
cp checkpoints/best.pt ../backend/models/best.pt
```

Then start the backend with demo mode disabled:

```bash
DEEPFAKE_DEMO_MODE=0 uvicorn app.main:app --reload --port 8000
```

## Format

`best.pt` is a Python pickle of `{ "state_dict": ..., "config": ..., "epoch": ..., "val_accuracy": ... }`.
The model architecture (`backend/app/ml/model.py`) is shared with
`model_training/train.py`, so checkpoints produced by the trainer load
without any architecture juggling.
