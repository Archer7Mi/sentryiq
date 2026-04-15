# SentryIQ

SentryIQ is an AI-powered SMB security MVP that combines technical vulnerability intelligence and human-risk simulation in one platform.

## What is in this repo

- `frontend/`: React + Vite + Tailwind dashboard for the demo experience
- `backend/`: FastAPI service for stack assessment, priority ranking, phishing simulation, and human-risk samples
- `docs/`: supporting notes and future product documentation

## Quick start

### Backend

1. Create a Python environment for `backend/`.
2. Install the backend dependencies from `backend/pyproject.toml`.
3. Run the API with `uvicorn sentryiq_api.main:app --reload --app-dir backend/src`.

### Frontend

1. Install the frontend dependencies in `frontend/`.
2. Run the UI with `npm run dev` from `frontend/`.

## MVP endpoints

- `GET /api/health`
- `POST /api/stack/assess`
- `POST /api/simulations/phishing`
- `GET /api/human-risk/sample`

## Notes

The first pass is intentionally scaffolded with deterministic demo logic so the product can be demonstrated before live API integrations are added.
