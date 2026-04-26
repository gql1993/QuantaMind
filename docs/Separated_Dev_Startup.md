# QuantaMind Separated Dev Startup

This guide starts the separated FastAPI backend and Vite frontend used by the new workspace.

## Prerequisites

- Python dependencies installed from `requirements.txt`
- Frontend dependencies installed in `frontend/`
- Optional desktop dependencies installed in `desktop/`

```powershell
pip install -r requirements.txt
npm --prefix frontend install
npm --prefix desktop install
```

## Start Backend + Frontend

From the repository root:

```powershell
.\start_separated_dev.bat
```

This opens two PowerShell windows:

- Backend: `http://127.0.0.1:18789`
- Frontend: `http://127.0.0.1:5173`

Optional flags:

```powershell
.\start_separated_dev.bat -BackendPort 18789 -FrontendPort 5173
.\start_separated_dev.bat -BuildFrontend
```

## Start Electron With The New Frontend

Build the frontend first, then start Electron:

```powershell
npm --prefix frontend run build
npm --prefix desktop start
```

For Vite development mode:

```powershell
set QUANTAMIND_DESKTOP_FRONTEND_URL=http://127.0.0.1:5173
npm --prefix desktop start
```

## Validation

```powershell
python -m pytest tests/test_separated_api.py
npm --prefix frontend run build
npm --prefix frontend run lint
```
