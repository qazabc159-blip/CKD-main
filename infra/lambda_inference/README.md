# Lambda Inference Handler

This folder contains the **first Lambda-oriented inference slice** for the CKD platform.

## Purpose

The handler mirrors the same inference contract already used by the local FastAPI prototype:

- `GET /health`
- `POST /predict`
- `POST /predict/research`
- `POST /predict/clinical`

## Entry Point

- `handler.lambda_handler`

## Current Scope

- parses API Gateway-style events
- handles CORS for browser requests
- dispatches requests by path and method
- reuses the same shared inference logic from:
  - `backend/service.py`
- can use:
  - packaged artifact files copied into the Lambda image
  - or S3-hosted artifacts when the relevant environment variables are provided

## Design Intent

This is the direct cloud-facing equivalent of the working local prototype:

- local prototype:
  - `backend/main.py`
- Lambda target:
  - `infra/lambda_inference/handler.py`

That means the frontend can keep the same request/response contract when the local backend is replaced with API Gateway + Lambda.

The current SAM template can optionally place this Lambda in private subnets. In that mode, artifact access should either remain packaged into the image or be backed by a NAT path or S3 gateway endpoint if the function needs to fetch bundle files from S3.

## Supporting Files

- `Dockerfile`
- `requirements-lambda.txt`

These are used by the SAM template to build a Lambda container image.

## Environment Variables

- `CKD_ALLOWED_ORIGIN`
- `CKD_MODEL_ARTIFACT_BUCKET`
- `CKD_MODEL_ARTIFACT_KEY`
- `CKD_MODEL_METADATA_KEY`
- `CKD_SETUP_SUMMARY_KEY`
- `CKD_MODEL_REGISTRY_KEY`
- `CKD_ACTIVE_MODEL_ID`

If the S3 variables are left empty, the handler falls back to the local registry or packaged artifact bundle. If `CKD_MODEL_REGISTRY_KEY` is set together with `CKD_MODEL_ARTIFACT_BUCKET`, the handler resolves the active serving bundle through the S3 registry record first.

## Not Included Yet

- SAM / CloudFormation template
- structured CloudWatch metrics
- latency test harness
- frontend-to-cloud integration wiring

The SAM template now lives at:

- `infra/template.yaml`

The remaining items are the next layer after the first deployable handler is in place.
