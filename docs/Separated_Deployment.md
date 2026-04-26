# QuantaMind Separated Deployment

This is a lightweight deployment skeleton for the separated FastAPI backend and React frontend.

## Services

- `backend`: FastAPI app from `backend.quantamind_api.app`
- `frontend`: Nginx serving `frontend/dist` and proxying `/api/*` to the backend service

## Build And Start

```powershell
docker compose up --build
```

Open:

- Frontend: `http://127.0.0.1:8080`
- Backend health: `http://127.0.0.1:18789/api/v1/health`

## Local Validation

```powershell
python -m pytest tests/test_separated_api.py
npm --prefix frontend run build
npm --prefix frontend run lint
```

## Notes

- This Compose file is intentionally minimal and uses demo in-memory data for new separated APIs.
- PostgreSQL, pgvector, MinIO, authentication, and persistent audit storage should be added as follow-up services.
- Do not mount local secret files into containers unless they are intentionally created from `.example` templates.
