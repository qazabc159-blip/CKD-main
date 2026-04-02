# Model Governance v2 Report

## Purpose

This work item extended the initial model registry into a lightweight governance layer suitable for the thesis platform. The goal was not to build a full enterprise MLOps control plane, but to add three concrete governance capabilities that were previously missing:

- approval before activation
- promotion audit trail
- rollback workflow

## What Was Added

### 1. Lifecycle-aware registry state

The registry was upgraded from a simple active-model record into a lifecycle-aware structure.

Supported statuses:

- `candidate`
- `approved`
- `active`
- `retired`

Additional governance metadata now includes:

- `approved_by`
- `approved_at`
- `approval_note`
- `last_promoted_by`
- `last_promoted_at`
- `promotion_note`

The live registry file is:

- `artifacts/model_registry/model_registry.json`

The schema file is:

- `artifacts/model_registry/model_registry_schema.json`

### 2. Append-only event log

An audit log was added at:

- `artifacts/model_registry/registry_events.jsonl`

This log captures governance actions as append-only JSON lines. The initial bootstrap events document:

- registry entry creation
- approval of the thesis-serving model
- promotion of the thesis-serving model to active

This creates an explicit trail of model lifecycle decisions rather than leaving active-model changes implicit.

### 3. Governance scripts

Three scripts were added under `infra/`:

- `approve_model.py`
- `promote_model.py`
- `rollback_model.py`

Their roles are:

- `approve_model.py`
  - moves a model from `candidate` to `approved`
  - records approver identity and approval note
- `promote_model.py`
  - promotes an approved model to `active`
  - demotes the previous active model back to `approved`
  - records the promotion event
- `rollback_model.py`
  - restores a previous approved model to `active`
  - uses the event log to infer a rollback target when possible
  - records the rollback event

### 4. Registry-aware upload flow

`infra/upload_model_artifact_bundle.py` was updated so that new bundle uploads remain compatible with the governance-enabled registry.

Current behavior:

- new registry entries are created as `candidate` by default
- activation during upload remains possible through `--activate`
- when activation is requested, approval and promotion metadata are written automatically
- the script still prints the matching SAM parameter overrides for deployment

## Verification

### Syntax verification

The following files passed Python compilation checks:

- `infra/model_registry_ops.py`
- `infra/approve_model.py`
- `infra/promote_model.py`
- `infra/rollback_model.py`
- `infra/upload_model_artifact_bundle.py`
- `backend/service.py`

### Serving-path regression check

After the governance upgrade, local serving still resolved correctly through the registry:

- `registry_enabled = true`
- `registry_version = 2.0`
- `artifact_source = registry_local`
- `active_model_id = autoprognosis-336-main-ultra-v1`

This confirmed that governance additions did not break the active inference path.

### End-to-end governance workflow test

An isolated temporary registry copy was created for validation. A shadow model entry was added in `candidate` status, and the following sequence was executed successfully:

1. approve candidate model
2. promote approved model to active
3. roll back to the previous active model

Observed outcome:

- approval event written successfully
- promotion event captured previous and new active model IDs
- rollback event restored the original active model
- post-rollback status returned to:
  - original model: `active`
  - shadow model: `approved`

This verified that the governance workflow is operational rather than purely declarative.

## Why This Matters for the Thesis

This governance upgrade improves the platform contribution in several thesis-relevant ways.

1. It makes model activation an explicit governed decision rather than a silent configuration change.
2. It introduces traceable lifecycle evidence for model transitions.
3. It creates a credible rollback path, which is important whenever a model-serving system is discussed in deployment-oriented terms.
4. It strengthens the claim that the platform moved beyond a single hard-coded demo artifact into a more modular and controllable serving architecture.

## Current Boundary

The governance layer is still intentionally lightweight. It does not yet include:

- multi-user approval roles
- external notification or ticketing
- cryptographic signing
- deployment-policy enforcement in CI/CD
- integration with a managed registry product

It should therefore be described as a prototype-level model governance layer with explicit approval, promotion tracking, and rollback capability, not as full production governance.

## Most Relevant Files

- `artifacts/model_registry/model_registry.json`
- `artifacts/model_registry/model_registry_schema.json`
- `artifacts/model_registry/registry_events.jsonl`
- `artifacts/model_registry/README.md`
- `infra/model_registry_ops.py`
- `infra/approve_model.py`
- `infra/promote_model.py`
- `infra/rollback_model.py`
- `infra/upload_model_artifact_bundle.py`
