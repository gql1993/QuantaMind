# QuantaMind Backend

This directory is the separated backend entry for QuantaMind.

The current implementation is intentionally thin: it exposes a clean FastAPI
application boundary while the existing `quantamind/` and `quantamind_v2/`
packages continue to provide the actual domain capabilities.

## Development

```bash
python -m backend.quantamind_api.app
```

Default URL:

```text
http://127.0.0.1:18789
```

## Migration Rules

- Keep orchestration, tools, data access, approvals, and audit logic in the backend.
- Keep UI state, routing, and presentation in `frontend/`.
- Do not move existing V1 modules in the first migration step.
- Add stable `/api/v1/*` routes before replacing legacy Web pages.
