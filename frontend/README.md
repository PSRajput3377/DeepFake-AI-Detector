# DeepFake AI Detector — Frontend

Modern React SPA for the DeepFake AI Detector. Built with **Vite 8 + React 19**,
**Tailwind CSS**, **Framer Motion**, **Recharts** and **react-router-dom**.

## Run locally

```bash
npm install
npm run dev          # http://localhost:5173
```

The dev server proxies `/api` and `/media` to `http://127.0.0.1:8000`, so make
sure the FastAPI backend is running too (see the top-level README).

## Scripts

| Script            | What it does                                |
| ----------------- | ------------------------------------------- |
| `npm run dev`     | Start the Vite dev server with HMR          |
| `npm run build`   | Produce a production build in `dist/`       |
| `npm run preview` | Preview the production build locally        |
| `npm run lint`    | ESLint over `src/` (errors fail the script) |

## Pointing at a different backend

For a deployed setup, set `VITE_API_BASE_URL` at build/dev time:

```bash
VITE_API_BASE_URL="https://api.example.com" npm run build
```

The axios client in `src/lib/api.js` will prefix all requests with that URL.

## Project layout

```
src/
├─ components/           UI primitives
├─ pages/                Route components (Home, Detector, About, NotFound)
├─ lib/                  api client, theme provider, PDF report generator
├─ App.jsx               Route table + AnimatePresence
├─ main.jsx              ReactDOM root + providers
└─ index.css             Tailwind base + glass / btn-primary utilities
```

## Theming

The site is dark by default but fully themed in `light` mode too. The toggle
lives in the navbar and persists to `localStorage` under `deepfake-theme`.
