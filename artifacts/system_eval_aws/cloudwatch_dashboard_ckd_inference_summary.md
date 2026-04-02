# CloudWatch monitoring upgraded

- Dashboard name: `CKD-Inference-Operational-Dashboard`
- Region: `ap-northeast-1`
- Stack: `ckd-inference-stack`
- Lambda: `ckd-inference-stack-CkdInferenceFunction-ljylRibeKzU5`
- API Gateway ID: `rrms3q06rb`
- Stage: `prod`
- Lambda log group: `/aws/lambda/ckd-inference-stack-CkdInferenceFunction-ljylRibeKzU5`
- API access log group: `/aws/apigateway/ckd-inference-httpapi-access`
- Dashboard URL: https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1#dashboards:name=CKD-Inference-Operational-Dashboard

## Included dashboard panels
- Lambda invocations, errors, throttles
- Lambda duration (p50 / p95 / max)
- API Gateway request volume and 4xx/5xx
- API latency and integration latency
- Route-level request counts and latency from access logs
- Recent API access logs
- Recent Lambda logs

## Created alarms
- `CKD-Lambda-Errors-Any`
- `CKD-API-5XX-Any`
- `CKD-Lambda-Duration-p95-High`

These alarms are currently created with `ActionsEnabled = false`, so they serve as observable monitoring thresholds without sending notifications.
