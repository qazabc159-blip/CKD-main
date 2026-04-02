# CKD Thesis Implementation Handoff for GPT

This note summarizes the AWS/platform implementation work that has actually been completed and can now be used to support thesis writing, especially for Sections 5.5 and 5.6. It is written as a factual handoff rather than a polished thesis paragraph.

## 1. Overall implementation status

The project is no longer only a design mockup or UI-only prototype. A minimal but functional cloud inference slice has been implemented and verified. The currently working live path is:

- Public/frontend UI
- API Gateway
- Lambda inference function
- S3 model artifact bundle
- prediction response returned to the UI

This means the thesis can now truthfully claim that a prototype-level AWS-backed inference service was implemented and tested.

However, the system should still be described as a **prototype-level implementation**, not a full production-grade clinical deployment.

## 2. What was actually implemented

### 2.1 Local backend prototype

A local inference backend was first built to validate the end-to-end request/response path before AWS deployment.

Implemented files:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\backend\main.py`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\backend\service.py`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\backend\api_contract.md`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\backend\local_to_aws_handoff.md`

Implemented endpoints:

- `GET /health`
- `POST /predict`
- `POST /predict/research`
- `POST /predict/clinical`

Purpose:

- validate the frontend contract
- validate model loading and response formatting
- provide a stable service layer that could later be reused by Lambda

### 2.2 Frontend to backend integration

The CKD Prediction Studio frontend was upgraded from mock/demo behavior to a real adapter-based architecture. The app supports:

- research inference mode
- clinical intake mode
- live backend/AWS endpoint configuration
- report export
- prediction history
- Cloud/AWS adapter settings

The frontend was successfully tested in the following path:

- UI input -> local backend -> prediction response
- UI input -> AWS endpoint -> prediction response

### 2.3 AWS inference slice

The AWS-backed inference slice was implemented with:

- API Gateway (HTTP API)
- Lambda container-based inference function
- S3 model artifact storage

Implemented infrastructure files:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\infra\template.yaml`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\infra\lambda_inference\handler.py`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\infra\lambda_inference\Dockerfile`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\infra\lambda_inference\requirements-lambda.txt`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\infra\upload_model_artifact_bundle.py`

### 2.4 Why Lambda container image was used

The model file itself is small, but the inference dependency stack is not trivial. The deployment decision was therefore driven primarily by Python/scientific dependencies rather than by raw model file size.

Approximate model sizes:

- `best_autoprognosis_model.pkl`: about `0.84 MB`
- `best_baseline_model.joblib`: about `0.16 MB`

The main deployment challenge was therefore:

- `autoprognosis==0.1.22`
- `scikit-learn==1.8.0`
- related scientific Python dependencies

Because of this, a Lambda **container image** approach was used rather than a simpler zip-only Lambda bundle.

### 2.5 S3 artifact bundle

Serving artifacts were uploaded to S3 bucket:

- `ckd-automl-artifacts-junxiang`

The serving bundle included:

- `best_autoprognosis_model.pkl`
- `best_autoprognosis_metadata.json`
- `setup_summary.json`
- `serving_bundle_manifest.json`

An additional ultra-minimal serving artifact path was also prepared to reduce cold-start burden and simplify runtime loading.

Relevant file:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\training\14_build_ultra_minimal_serving_artifact_336.py`

Manifest:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\statistics_336\serving_bundle_manifest_ultra.json`

## 3. What was successfully verified

### 3.1 Live AWS endpoints

The deployed API base URL is:

- `https://rrms3q06rb.execute-api.ap-northeast-1.amazonaws.com/prod`

Verified routes:

- `GET /health`
- `POST /predict/research`
- `POST /predict/clinical`

All of these were tested successfully.

### 3.2 Research route

The `research` route is the thesis-faithful inference path because it directly uses the current Dataset #336 schema-aligned feature space.

Verified returned metadata includes:

- `Live API response`
- `model_version = autoprognosis-336-main::research`
- `serving_route = /predict/research`

This is the strongest implementation evidence for the thesis main line.

### 3.3 Clinical route

The `clinical` route also works live, but it should be described carefully.

Verified returned metadata includes:

- `model_version = autoprognosis-336-clinical-adapter-v1`
- `serving_route = /predict/clinical`

Important limitation:

This is **not** a separate native clinical model. It is a **provisional clinical-to-research adapter** that translates clinically familiar intake fields into the currently supported research inference path.

Therefore, it is acceptable to describe the clinical route as:

- an implementation-oriented intake adapter
- a product-facing inference entry path
- a provisional adapter rather than a finalized clinical schema

## 4. Monitoring and observability

CloudWatch monitoring was upgraded beyond simple logs.

### 4.1 Dashboard

Dashboard name:

- `CKD-Inference-Operational-Dashboard`

Dashboard URL:

- `https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1#dashboards:name=CKD-Inference-Operational-Dashboard`

Dashboard definition:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\cloudwatch_dashboard_ckd_inference.json`

Summary:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\cloudwatch_dashboard_ckd_inference_summary.md`

Included panels:

- Lambda invocations, errors, throttles
- Lambda duration (`p50 / p95 / max`)
- API request volume and `4xx / 5xx`
- API latency vs integration latency
- route-level request counts and latency via access logs
- recent API access logs
- recent Lambda logs

### 4.2 Access logs

API access logs were enabled for the `prod` stage and written to:

- `/aws/apigateway/ckd-inference-httpapi-access`

Lambda logs are written to:

- `/aws/lambda/ckd-inference-stack-CkdInferenceFunction-ljylRibeKzU5`

This is useful for demonstrating that `/predict/research`, `/predict/clinical`, and `/health` were actually hit.

### 4.3 Alarms

Created alarms:

- `CKD-Lambda-Errors-Any`
- `CKD-API-5XX-Any`
- `CKD-Lambda-Duration-p95-High`

Alarm definition archive:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\cloudwatch_alarms_ckd_inference.json`

Current status:

- alarms exist
- `ActionsEnabled = false`

This means they currently function as observable thresholds rather than active notification pipelines.

## 5. Latency evidence

Latency measurement script:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\infra\measure_lambda_latency.py`

Latency outputs:

- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_latency_summary.md`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_latency_summary.json`
- `C:\Users\User\Desktop\小楊機密\碩士論文\最重要論文檔\CKD-main\artifacts\system_eval_aws\lambda_latency_samples.csv`

Current summary values:

### Research route warm latency

- mean: `135.11 ms`
- median: `133.38 ms`
- p95: `158.50 ms`
- max: `204.38 ms`
- success: `20/20`

### Clinical route warm latency

- mean: `126.22 ms`
- median: `125.60 ms`
- p95: `133.29 ms`
- max: `134.71 ms`
- success: `20/20`

### Example cold-start evidence from CloudWatch

- total duration: `2006.29 ms`
- init duration: `718.82 ms`

Interpretation:

- warm requests are roughly in the `100–200 ms` range
- cold start is in the `~2 second` range based on the current evidence

## 6. Public frontend hosting status

The publicly accessible frontend is currently hosted on Cloudflare Pages, not on S3 + CloudFront + Route 53.

Public URLs:

- `https://d5a6fa81.ckd-automl-platform.pages.dev/`
- `https://d5a6fa81.ckd-automl-platform.pages.dev/app/`

Important interpretation:

- frontend hosting is public and functional
- AWS handles the inference slice
- but the static frontend hosting path is **not** currently AWS-native

Therefore:

- the inference architecture is genuinely AWS-backed
- the frontend hosting architecture is still Cloudflare-based

This should be treated as a limitation or design gap relative to the original all-AWS target architecture.

## 7. What the implementation now supports in thesis writing

The thesis can now truthfully claim:

1. A live prototype-level cloud inference path was implemented.
2. The frontend can submit requests to a deployed AWS API.
3. API Gateway, Lambda, and S3-hosted model artifacts were integrated.
4. Both route availability and runtime behavior were monitored through CloudWatch.
5. Initial latency evidence was collected for warm requests and recent cold-start behavior.

## 8. What still remains incomplete relative to the full architecture figure

The following parts of the original AWS architecture are not yet fully realized:

### Not yet fully implemented

- Route 53
- CloudFront
- S3 static website hosting for the frontend
- VPC / private subnet deployment of Lambda
- SageMaker training job as a verified cloud training path
- formal model registry workflow
- EC2 backup training environment
- CI/CD pipeline
- more formal IAM hardening / least-privilege refinement

### Partially implemented

- CloudWatch monitoring: implemented, but alert notifications are not yet wired
- model metadata / serving manifest: implemented, but not yet a full registry

## 9. Safe wording for the thesis

The implementation should be described using wording such as:

- `prototype-level but functional cloud inference slice`
- `minimal AWS-backed deployment path`
- `implementation-aware prototype architecture`

Avoid describing the platform as:

- `full production deployment`
- `production-grade clinical system`
- `fully automated MLOps platform`

## 10. Strongest evidence for Section 5.5

The most useful evidence set for Section 5.5 is:

1. Public app screenshot showing:
   - `Live API response`
   - `Model version`
   - `Serving route`
2. CloudWatch panel:
   - `Lambda duration (p50 / p95 / max)`
3. CloudWatch panel:
   - `API latency vs integration latency`
4. CloudWatch panel:
   - `API Gateway request volume and errors`
5. CloudWatch log/table panel:
   - `Route-level request counts and latency (access logs)`

## 11. Suggested thesis interpretation boundary

The implementation evidence is strong enough to support a real prototype platform section, but not a full-production claim.

The most accurate one-sentence summary is:

> A minimal but functional AWS-backed inference path was implemented, connecting the public UI, API Gateway, Lambda-based model serving, and S3-hosted model artifacts, while the broader platform remains at the prototype architecture stage rather than a complete production deployment.
