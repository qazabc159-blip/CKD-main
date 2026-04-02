# CKD Prediction Prototype API Contract

## Status

This document describes the **implemented local prototype contract** for the CKD Prediction Studio backend.

- Local prototype status: implemented
- AWS deployment status: not implemented yet
- Purpose: provide a stable request/response shape that the current frontend can use before the same inference path is migrated behind API Gateway and Lambda

## Implemented Endpoints

- `GET /health`
- `POST /predict`
- `POST /predict/research`
- `POST /predict/clinical`

## Request Shape

All prediction endpoints accept the same top-level shape:

```json
{
  "mode": "research",
  "inputs": {
    "age": 55,
    "sg": 1.02,
    "al": 2,
    "su": 0
  },
  "context": {
    "case_id": "CKD-OPS-0001",
    "patient_name": "王OO",
    "clinical_note": "Research-mode prototype request"
  }
}
```

## Request Notes

- `mode` is required for `POST /predict`, but may be omitted when calling the route-specific endpoints directly.
- `inputs` is the primary request envelope used by the current frontend.
- `context` is optional and currently used for UI framing, tracing, and report generation.
- Missing values are allowed and are passed through as `null`.

## Route Semantics

### `POST /predict/research`

- Uses the current Dataset #336 research feature space directly.
- Loads the current AutoPrognosis artifact from:
  - `artifacts/autoprognosis_336/best_autoprognosis_model.pkl`
- Intended to be the most faithful route for the current thesis modeling line.

### `POST /predict/clinical`

- Accepts clinically familiar intake variables from the dual-mode UI.
- Uses a **provisional clinical-to-research adapter** before inference.
- This route is implementation-oriented and should not be interpreted as a finalized clinical schema.

### `POST /predict`

- Dispatches to the correct path based on `mode`.

## Response Shape

```json
{
  "risk_score": 0.9472,
  "prediction_label": "high_risk",
  "model_version": "autoprognosis-336-main::research",
  "serving_route": "/predict/research",
  "timestamp": "2026-03-26T08:30:00Z",
  "notes": "Live local inference completed with the current Dataset #336 AutoPrognosis artifact.",
  "explanation": [
    {
      "feature": "sc",
      "message": "Higher serum creatinine increased the returned risk profile.",
      "contribution": 0.11
    }
  ]
}
```

## Response Notes

- `risk_score` is a probability-like value in `[0, 1]`.
- `prediction_label` currently uses:
  - `lower_risk`
  - `moderate_risk`
  - `high_risk`
- `model_version` identifies the serving route used by the prototype.
- `serving_route` echoes the route that produced the result.
- `notes` explains whether the request used direct research inference or a provisional clinical adapter.
- `explanation` is currently an **operational UI summary**, not a formal SHAP export.

## Health Check

`GET /health` returns a lightweight service status response for smoke testing.

## Explicit Non-Claims

- This contract documents a **local prototype backend**, not a production clinical deployment.
- The `clinical` route currently relies on conservative field translation and should not be described as a finalized clinical inference schema.
- API Gateway, Lambda, and S3 deployment are the next migration target for this contract, not proof of current cloud deployment.
