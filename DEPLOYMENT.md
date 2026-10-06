# Deployment Guide

This project deploys as two separate services:

- Backend: Render web service (Python/FastAPI)
- Frontend: Vercel static app (Vite build)

The app uses the Azure CPU dataset, a leakage-safe feature pipeline, and serialized model artifacts already checked into the backend ML directory. The backend reads `backend/ml/data/processed/test.csv` at runtime; because that file is generated locally and not stored in Git, it must be regenerated during deployment before the app starts.

## Render backend setup

### Required environment variables

Set the following in the Render service dashboard:

- `FRONTEND_URL`: The public frontend origin, for example `https://cloudpulse.example.com`
  - This is read by the backend to configure FastAPI CORS.
  - If unset, the backend defaults to `*` for local development compatibility.

### Build and start commands

Use the following service settings:

- Root directory: `backend`
- Build command:
  ```bash
  pip install -r requirements.txt
  python ml/data/download.py
  python ml/data/prepare.py
  ```
- Start command:
  ```bash
  uvicorn app:app --host 0.0.0.0 --port $PORT
  ```

### Why `test.csv` is regenerated at deploy time

The app runtime reads `backend/ml/data/processed/test.csv` directly, and the file is generated from the downloaded Azure dataset shard. It is not version-controlled in the repo and must exist on the Render server before the app can serve resource data.

`train.csv` is not read by `backend/app.py` during runtime; it is used offline for model training. Because of that, it does not need to be regenerated on every deploy. The runtime requirement is only `test.csv`.

### First deploy timing note

`download.py` downloads a ~227 MB Azure shard, and `prepare.py` then builds the processed test dataset. This makes the first deploy noticeably slower than a normal Python app deploy. Allow roughly 5-10 minutes on the first deployment, depending on network speed and Render compute availability. This is expected and required for the app to function correctly.

## Vercel frontend setup

### Required environment variable

In the Vercel project settings, set:

- `VITE_API_URL`: the live Render backend URL, for example `https://cloudpulse-backend.onrender.com`

### Build settings

Use these Vercel project settings:

- Framework preset: `Vite`
- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Output directory: `dist`

Do not configure `/api/*` rewrites to a Vercel-hosted function because the API is now hosted on Render. The frontend should talk directly to the Render HTTPS URL via `VITE_API_URL`.

## Deployment order

1. Deploy the backend to Render first.
2. Copy the live Render URL from the backend service.
3. Set `VITE_API_URL` in the Vercel project to that live Render URL.
4. Deploy the frontend to Vercel.

This keeps the API and frontend separated correctly while allowing the frontend to call the Render-hosted backend.

## Deployment configuration summary

- Backend service: Render (`backend/` root, Python app)
- Frontend service: Vercel (`frontend/` root, static Vite build)
- Backend CORS: controlled by `FRONTEND_URL`
- Frontend API base: controlled by `VITE_API_URL`
- Data generation: triggered during backend build to ensure `processed/test.csv` exists before startup
