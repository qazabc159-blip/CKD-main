# Backend

This folder now contains the **minimal local inference slice** for the CKD Prediction Studio.

## Current Scope

- receive prediction requests from the current frontend
- support both:
  - research inference mode
  - clinical intake mode
- load the current Dataset #336 AutoPrognosis artifact
- support registry-driven active-model selection
- return a structured prediction response for the UI

## Implemented Files

- `main.py`: FastAPI application for local inference
- `api_contract.md`: implemented prototype contract

## Current Status

Implemented as a **local prototype backend**.

This is the first working slice that can later be migrated to:
- API Gateway
- Lambda inference
- S3-hosted model artifacts

## Run Locally

From the repository root:

```bash
uvicorn backend.main:app --reload
```

Default local URL:

- `http://127.0.0.1:8000`

Useful endpoints:

- `GET /health`
- `POST /predict`
- `POST /predict/research`
- `POST /predict/clinical`

## Frontend Integration

The current frontend can use this backend by setting:

- API base URL: `http://127.0.0.1:8000`
- Clinical path: `/predict/clinical`
- Research path: `/predict/research`
- Request envelope: `inputs`
- Mock mode: off

## Important Notes

- The `research` route is the most faithful route for the current thesis modeling line.
- The `clinical` route currently uses a conservative adapter into the research feature space.
- If `artifacts/model_registry/model_registry.json` exists, the backend resolves the active model through the registry before falling back to packaged defaults.
- This backend is intended to create a defensible implementation path for the thesis platform; it is not yet a production clinical service.
