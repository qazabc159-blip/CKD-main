# Chapter 5.5 AWS implementation evidence checklist

## Core deployment evidence
- Public showcase/app URL is reachable and the app can switch to a live AWS endpoint.
- API Gateway base URL is active: `https://rrms3q06rb.execute-api.ap-northeast-1.amazonaws.com/prod`.
- Lambda-backed routes respond successfully:
  - `/health`
  - `/predict/research`
  - `/predict/clinical`
- Lambda reads the serving artifact bundle from S3 bucket `ckd-automl-artifacts-junxiang`.
- Research-mode UI shows `Live API response`, a concrete `Model version`, and a concrete `Serving route`.
- Clinical-mode UI also returns a live response through the provisional clinical adapter.

## Artifact and configuration evidence
- SAM template exists and was used to deploy the inference slice:
  - `C:/Users/User/Desktop/????/????/??????/CKD-main/infra/template.yaml`
- Lambda handler exists:
  - `C:/Users/User/Desktop/????/????/??????/CKD-main/infra/lambda_inference/handler.py`
- S3 upload script exists:
  - `C:/Users/User/Desktop/????/????/??????/CKD-main/infra/upload_model_artifact_bundle.py`
- Serving manifest exists:
  - `C:/Users/User/Desktop/????/????/??????/CKD-main/artifacts/statistics_336/serving_bundle_manifest_ultra.json`

## Performance evidence
- Warm latency summary exists:
  - `C:/Users/User/Desktop/????/????/??????/CKD-main/artifacts/system_eval_aws/lambda_latency_summary.md`
- Raw latency samples exist:
  - `C:/Users/User/Desktop/????/????/??????/CKD-main/artifacts/system_eval_aws/lambda_latency_samples.csv`
- Recent cold-start evidence exists in CloudWatch logs.

## Monitoring evidence
- CloudWatch dashboard deployed:
  - `CKD-Inference-Operational-Dashboard`
- Dashboard definition archived locally:
  - `C:/Users/User/Desktop/????/????/??????/CKD-main/artifacts/system_eval_aws/cloudwatch_dashboard_ckd_inference.json`
- API access logs enabled at stage `prod` and written to:
  - `/aws/apigateway/ckd-inference-httpapi-access`
- Lambda logs available in:
  - `/aws/lambda/ckd-inference-stack-CkdInferenceFunction-ljylRibeKzU5`
- Alarms created:
  - `CKD-Lambda-Errors-Any`
  - `CKD-API-5XX-Any`
  - `CKD-Lambda-Duration-p95-High`

## Recommended screenshots for Section 5.5
- Screenshot 1: Public app showing `Live API response`, `Model version`, and `Serving route`.
- Screenshot 2: CloudWatch dashboard upper panels (Lambda/API latency and error metrics).
- Screenshot 3: CloudWatch dashboard route-level access-log panel.
- Screenshot 4: API Gateway route list or Lambda configuration page if you want a configuration-oriented figure.

## Honest wording boundary
Use wording such as `prototype-level but functional cloud inference slice` or `minimal AWS-backed deployment path`. Avoid describing the platform as a full production-grade clinical deployment.
