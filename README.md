# DeepFake AI Detector

End-to-end deepfake video detection built around a hybrid
**ResNeXt + LSTM + MobileViT** pipeline. Upload a video, get a verdict
with frame-level evidence and a downloadable PDF report.

## Project layout

| Layer            | Stack                                                          | Path             |
| ---------------- | -------------------------------------------------------------- | ---------------- |
| **Frontend**     | React 19, Vite 8, TailwindCSS, Framer Motion, Recharts         | `frontend/`      |
| **Backend**      | FastAPI, Uvicorn (ASGI), PyTorch (lazy), OpenCV, pydantic v2   | `backend/`       |
| **Training**     | PyTorch trainer for the spatial-temporal model                 | `model_training/`|
| Dataset          | SDFVD — 53 real + 53 fake videos, used for the smoke training  | `SDFVD/`         |

> **Demo mode is on by default.** You can run the entire SPA + API without
> any trained `.pt` weights — a deterministic heuristic predictor keeps the
> pipeline live, so you can demo every screen end-to-end.

---

## Quickstart

You'll need **Python 3.10+** and **Node 18+**.

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit:

| URL                                          | What it is                          |
| -------------------------------------------- | ----------------------------------- |
| http://localhost:8000/docs                   | **Swagger UI** (interactive)        |
| http://localhost:8000/redoc                  | ReDoc reference                     |
| http://localhost:8000/api/health             | Health probe                        |
| http://localhost:8000/api/predict            | Main inference endpoint             |

### 2. Frontend (React SPA)

In a second terminal:

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

Vite proxies `/api` and `/media` to the FastAPI backend.

### 3. Train the model on SDFVD

```bash
cd model_training
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1. extract face crops once (writes to processed_faces/)
python preprocess.py --data ../SDFVD --out processed_faces

# 2. train
python train.py --data processed_faces --epochs 30 --batch-size 4

# 3. evaluate (writes confusion matrix + metrics.json)
python evaluate.py --data processed_faces --weights checkpoints/best.pt
```

After training, drop `checkpoints/best.pt` into `backend/models/` and start
the backend with `DEEPFAKE_DEMO_MODE=0` to switch from demo mode to real
inference.

See `model_training/README.md` for the full trainer manual (config flags,
data augmentation, multi-GPU notes, scaling to FaceForensics++).

---

## Architecture

```
Video ──► Frame sampling ──► MTCNN face crop (224×224)
                                   │
                                   ▼
                          ResNeXt-50 32x4d (ImageNet-pretrained)
                                   │      (feature 2048-d / frame)
                                   ▼
                            Linear projection → 512-d
                                   │
                                   ▼
                                  LSTM
                                   │
                                   ▼
                       MobileViT global refinement
                                   │
                                   ▼
                       Mean-pool over time + Dropout
                                   │
                                   ▼
                       Linear (512 → 2)  ─►  [REAL, FAKE]
```

Why this works:

- **ResNeXt-50** captures per-frame spatial artifacts (texture, blending
  edges, frequency anomalies).
- **LSTM** models temporal context across the frame sequence, catching the
  temporal seams generators leave between frames.
- **MobileViT** applies lightweight global attention over the sequence,
  giving long-range context the LSTM alone can't model.
- **224×224 input** matches what the ImageNet-pretrained backbone expects
  for maximum transfer learning benefit.

---

## What's inside the SPA

- **Home** — animated hero, feature grid, how-it-works walkthrough,
  architecture diagram, animated preview card.
- **Detector** — drag-and-drop uploader, sequence-length slider, multi-stage
  analysis pipeline, smooth scroll-to-result, confidence ring, per-frame
  probability chart, sampled-frame and cropped-face galleries, downloadable
  PDF report, "analyze another" reset.
- **How it works** — deeper dive on the model, datasets, FastAPI/Uvicorn
  performance story, direct link to the auto-generated Swagger UI.
- Dark/light mode, mobile-first nav, toast notifications.

## What's inside the API

- ASGI under Uvicorn: async, fast, streaming uploads.
- Auto-generated OpenAPI docs at `/docs` and `/redoc`.
- `DemoPredictor` — model-free deterministic verdicts (file hash + OpenCV
  signal features). Same video → same answer.
- `RealPredictor` — wraps the trained ResNeXt + LSTM + MobileViT model.
- MTCNN face detection (matches training preprocessing exactly), with
  OpenCV Haar cascade as a graceful fallback.
- Heavy CV/ML work runs in a worker thread (`asyncio.to_thread`) so the
  event loop stays responsive.
