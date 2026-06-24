# DeepFake AI Detector — Backend (FastAPI)

A small async API that powers the React SPA. Built on **FastAPI + Uvicorn**,
with **lazy ML imports** so the server starts even on machines without
PyTorch / dlib installed.

## Highlights

- ⚡️ **ASGI under Uvicorn** — fast, async, supports streaming uploads.
- 📚 **Auto-generated OpenAPI docs** at [`/docs`](http://localhost:8000/docs)
  and ReDoc at [`/redoc`](http://localhost:8000/redoc).
- 🎭 **Demo Mode by default** — deterministic verdicts without any `.pt`
  weights, so the API works end-to-end out of the box.
- 🧠 **Real predictor** — drop trained
  **ResNeXt-50 + LSTM + MobileViT** weights into `models/best.pt` and
  disable demo mode to switch over (the same model class is shared with
  `model_training/`).
- 🧰 **MTCNN face detection** with graceful fallbacks — MTCNN
  (`facenet-pytorch`) is preferred (matches training preprocessing); falls
  back to `face_recognition` (dlib) and finally OpenCV's bundled Haar
  cascade. No painful dlib install required.
- 🧵 **CPU-bound work runs in a thread pool** (`asyncio.to_thread`) so the
  event loop stays responsive.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Now visit:

| URL                                     | What it is                |
| --------------------------------------- | ------------------------- |
| http://localhost:8000/docs              | Swagger UI (interactive)  |
| http://localhost:8000/redoc             | ReDoc reference           |
| http://localhost:8000/api/health        | Quick health probe        |
| http://localhost:8000/api/predict       | The main inference route  |

## Endpoints

### `GET /api/health`

```json
{
  "status": "ok",
  "version": "1.0.0",
  "demo_mode": true,
  "torch": true,
  "face_detector": "mtcnn",
  "mtcnn": true,
  "face_recognition": false
}
```

### `POST /api/predict`

`multipart/form-data` upload.

| Field             | Type    | Required | Description                       |
| ----------------- | ------- | -------- | --------------------------------- |
| `file`            | file    | yes      | Video file (≤ 100 MB)             |
| `sequence_length` | integer | no       | Frames to sample (default: `20`)  |

Sample response (truncated):

```json
{
  "label": "FAKE",
  "confidence": 0.84,
  "real_prob": 0.16,
  "fake_prob": 0.84,
  "per_frame_fake_prob": [0.42, 0.51, 0.78, ...],
  "frames_analyzed": 20,
  "faces_detected": 6,
  "sequence_length": 20,
  "elapsed_ms": 1421,
  "video_url": "/media/uploaded_videos/1714.....mp4",
  "preview_frames": ["/media/uploaded_images/<id>/frame_000.jpg", ...],
  "face_crops":     ["/media/uploaded_images/<id>/face_001.jpg", ...],
  "model": "DemoPredictor (heuristic)",
  "demo_mode": true,
  "upload_id": "9f3a0c7b1d2e",
  "filename": "test.mp4",
  "size_bytes": 4098123
}
```

## Configuration

All settings can be tweaked via environment variables (or a `.env` file in
this directory). Variables are prefixed with `DEEPFAKE_`.

| Env var                          | Default                            | Notes                                              |
| -------------------------------- | ---------------------------------- | -------------------------------------------------- |
| `DEEPFAKE_DEMO_MODE`             | `true`                             | Set to `false` to use real `.pt` weights           |
| `DEEPFAKE_MAX_UPLOAD_BYTES`      | `104857600` (100 MB)               | Per-upload size cap                                |
| `DEEPFAKE_DEFAULT_SEQUENCE_LENGTH` | `20`                             | Default frames analyzed                            |
| `DEEPFAKE_MAX_SEQUENCE_LENGTH`   | `100`                              | Hard upper bound                                   |
| `DEEPFAKE_CORS_ALLOW_ALL`        | `true`                             | Allow any origin (handy for demos)                 |
| `DEEPFAKE_CORS_ORIGINS`          | localhost:5173, 127.0.0.1:5173, …  | JSON list, used when `CORS_ALLOW_ALL=false`        |

## Layout

```
backend/
├─ app/
│  ├─ main.py            FastAPI app + routes
│  ├─ config.py          pydantic-settings configuration
│  └─ ml/
│     ├─ model.py        DeepFakeDetector (ResNeXt + LSTM + MobileViT)
│     ├─ frames.py       evenly-spaced frame extraction
│     ├─ faces.py        face detection (MTCNN → dlib → Haar)
│     └─ predictors.py   DemoPredictor + RealPredictor (+ factory)
├─ media/                runtime uploads + preview frames (auto-created)
├─ models/               drop your .pt files here (see models/README.md)
├─ requirements.txt
└─ README.md
```

> The `DeepFakeDetector` class is shared with `model_training/` — the
> trainer imports it from this same module, so any `.pt` produced by the
> trainer is loadable by the backend with no architecture mismatch.
