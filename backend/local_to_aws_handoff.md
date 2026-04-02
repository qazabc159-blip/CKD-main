# Local-to-AWS Handoff Notes

This note maps the working local backend slice to the AWS architecture shown in the thesis.

## What Is Working Locally

- frontend request shape is defined
- backend routes are callable:
  - `POST /predict/research`
  - `POST /predict/clinical`
- the current Dataset #336 AutoPrognosis artifact can be loaded and used for inference
- the backend returns UI-ready JSON

## How This Maps to the AWS Diagram

### Current local prototype

- `web/app/index.html`
- `backend/main.py`
- local model artifact from:
  - `artifacts/autoprognosis_336/best_autoprognosis_model.pkl`

### AWS migration target

- `CKD Web UI` stays as the static frontend
- `API Gateway` exposes the same request/response contract
- `CKD Inference Lambda` replaces the local FastAPI route handler
- `ckd-model bucket` stores the model artifact and metadata
- first deployment template:
  - `infra/template.yaml`

## Keep the Same Contract

The easiest migration path is to preserve:

- request fields:
  - `mode`
  - `inputs`
  - `context`
- response fields:
  - `risk_score`
  - `prediction_label`
  - `model_version`
  - `serving_route`
  - `timestamp`
  - `notes`
  - `explanation`

If this shape stays stable, the frontend does not need a structural rewrite when the backend moves to AWS.

## Recommended Next AWS Steps

1. Upload the serving artifact to the model bucket.
2. Port `backend/main.py` inference logic into a Lambda handler.
3. Expose:
   - `/predict/research`
   - `/predict/clinical`
   through API Gateway.
4. Point the frontend to the API Gateway base URL and disable mock mode.
5. Collect:
   - request/response screenshots
   - CloudWatch execution logs
   - latency statistics

## Scope Reminder

This handoff note is intentionally limited to the **inference path**.
It does not require:

- SageMaker pipeline automation
- full CI/CD
- complete model registry implementation
- production IAM hardening

Those can remain future layers after the thesis-critical inference path is running.
