# QuantaMind CI

The repository uses GitHub Actions for a lightweight CI baseline.

## Workflow

Workflow file:

```text
.github/workflows/ci.yml
```

It runs on pushes and pull requests targeting `main`.

## Jobs

- `Separated API tests`
  - Installs Python dependencies from `requirements.txt`
  - Runs `python -m pytest tests/test_separated_api.py`
- `Frontend build and lint`
  - Installs frontend dependencies with `npm ci`
  - Runs `npm run lint`
  - Runs `npm run build`
- `Desktop script syntax`
  - Checks Electron scripts with `node -c`

## Local Equivalent

```powershell
python -m pytest tests/test_separated_api.py
npm --prefix frontend run lint
npm --prefix frontend run build
cd desktop
node -c main.js
node -c preload.js
```

Docker validation remains optional because developer machines and CI runners may not always have Docker available.
