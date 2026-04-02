# Model Registry

This folder contains the first registry layer for the thesis-serving CKD platform.

## Files

- `model_registry.json`: active registry record used by local and registry-aware serving.
- `model_registry_schema.json`: lightweight JSON schema for structure validation and documentation.
- `registry_events.jsonl`: append-only audit trail for approval, promotion, and rollback events.

## Current Active Model

- `model_id`: `autoprognosis-336-main-ultra-v1`
- `version`: `1.0.0`
- `response_model_version_base`: `autoprognosis-336-main`
- `clinical_adapter_version`: `autoprognosis-336-clinical-adapter-v1`

## Design Intent

The registry is intentionally minimal. It is meant to:

- decouple serving from hard-coded artifact paths
- expose an explicit active model identifier
- keep local and S3 bundle metadata aligned
- record lightweight governance actions
- provide a clean handoff point for future registry governance work

## Governance v2

The current registry layer now supports a lightweight governance lifecycle:

- `candidate`
- `approved`
- `active`
- `retired`

Supporting scripts:

- `infra/approve_model.py`
- `infra/promote_model.py`
- `infra/rollback_model.py`

This is still not a full production model-governance system, but it is sufficient to demonstrate:

- approval before activation
- promotion tracking
- rollback capability
- append-only audit evidence
