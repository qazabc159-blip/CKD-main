# Model Registry Implementation Report

## Scope

This report records the first model-registry implementation for the CKD thesis platform. The goal of this work item was to move the serving path beyond hard-coded artifact selection and establish an explicit active-model layer that can later support stronger model governance.

## What Was Implemented

### 1. Registry-aware serving logic

The shared serving logic in `backend/service.py` was extended to resolve the active model through a registry when available.

Implemented behavior:

- local registry path:
  - `artifacts/model_registry/model_registry.json`
- optional S3 registry path:
  - supplied through `CKD_MODEL_ARTIFACT_BUCKET` and `CKD_MODEL_REGISTRY_KEY`
- optional active-model override:
  - `CKD_ACTIVE_MODEL_ID`

Serving precedence is now:

1. registry-driven S3 bundle
2. registry-driven local bundle
3. legacy direct S3 artifact wiring
4. packaged artifact defaults

This preserves backward compatibility while enabling explicit model selection.

### 2. Registry file and schema

A minimal registry layer was added under:

- `artifacts/model_registry/model_registry.json`
- `artifacts/model_registry/model_registry_schema.json`

The initial active record is:

- `model_id`: `autoprognosis-336-main-ultra-v1`
- `version`: `1.0.0`
- `display_name`: `Dataset #336 AutoPrognosis ultra-minimal serving bundle`

The record includes:

- local serving bundle paths
- S3 serving bundle paths
- active serving labels for the research and clinical routes
- provenance pointers to the existing metadata and manifest files

### 3. SAM template support

The SAM template was extended with:

- `ModelRegistryKey`
- `ActiveModelId`

and corresponding Lambda environment variables:

- `CKD_MODEL_REGISTRY_KEY`
- `CKD_ACTIVE_MODEL_ID`

This allows the deployed Lambda to switch from direct artifact-key wiring to registry-driven model resolution.

### 4. Registry-aware upload helper

`infra/upload_model_artifact_bundle.py` was expanded so that it can now:

- upload the serving bundle to S3
- write or update the local registry file
- optionally upload `model_registry.json` to S3
- print SAM parameter overrides including:
  - `ModelRegistryKey`
  - `ActiveModelId`

The script now defaults to the current thesis-serving artifact:

- `artifacts/autoprognosis_336/serving_ultra_minimal.pkl`

## Verification

The following checks were completed locally.

### Syntax checks

- `backend/service.py`: passed `py_compile`
- `infra/upload_model_artifact_bundle.py`: passed `py_compile`

### Registry resolution check

The backend was imported locally and confirmed to:

- resolve `artifacts/model_registry/model_registry.json`
- identify `autoprognosis-336-main-ultra-v1` as the active model
- load the local ultra-minimal serving bundle through the registry
- report `artifact_source = registry_local` in the health payload

### Prediction-path check

A direct local call to `build_research_response(...)` was executed successfully under registry-driven mode. The returned payload confirmed:

- `model_version = autoprognosis-336-main::research`
- `serving_route = /predict/research`
- active prediction executed through the registry-selected serving artifact

## Practical Thesis Value

This work item materially strengthens the platform contribution of the thesis in three ways.

1. It makes model selection explicit rather than implicit.
2. It creates a clean bridge between artifact management and deployment configuration.
3. It provides a concrete foundation for later model-governance work without requiring a full production registry implementation.

## Current Boundary

This is still a minimal registry layer rather than a complete production model registry. It does not yet provide:

- approval workflow
- rollback history
- audit trail of model promotions
- registry-backed training orchestration
- role-based governance controls

The current implementation should therefore be described as a prototype-level model registry that improves deployment realism and platform modularity, but does not yet constitute full model-governance maturity.

## Most Relevant Files

- `backend/service.py`
- `infra/template.yaml`
- `infra/upload_model_artifact_bundle.py`
- `artifacts/model_registry/model_registry.json`
- `artifacts/model_registry/model_registry_schema.json`
- `artifacts/model_registry/README.md`
