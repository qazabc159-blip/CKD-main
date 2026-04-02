# AWS Inference Latency Summary

- Generated at: `2026-03-27T16:46:55Z`
- Base URL: `https://rrms3q06rb.execute-api.ap-northeast-1.amazonaws.com/prod`
- Lambda function: `ckd-inference-stack-CkdInferenceFunction-ljylRibeKzU5`
- Warm-up runs per route: `2`
- Measured warm runs per route: `20`

## Warm Latency

| Route | Mean (ms) | Median (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) | Success / Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| research | 135.11 | 133.38 | 133.38 | 158.5 | 195.2 | 119.25 | 204.38 | 20 / 20 |
| clinical | 126.22 | 125.6 | 125.6 | 133.29 | 134.43 | 118.6 | 134.71 | 20 / 20 |

## Recent Cold-Start Evidence from CloudWatch

| Timestamp (UTC) | Duration (ms) | Init Duration (ms) | Billed (ms) | Max Memory (MB) | Note |
|---|---:|---:|---:|---:|---|
| 2026-03-27T16:46:47Z | 2006.29 | 718.82 | 2726.00 | 293 | CloudWatch REPORT with Init Duration; current handler does not log request path. |
| 2026-03-27T16:18:39Z | 1.71 | 782.77 | 785.00 | 116 | CloudWatch REPORT with Init Duration; current handler does not log request path. |
| 2026-03-27T16:18:39Z | 1.31 | 792.57 | 794.00 | 116 | CloudWatch REPORT with Init Duration; current handler does not log request path. |
| 2026-03-27T16:06:58Z | 4346.51 | 1482.76 | 5830.00 | 293 | CloudWatch REPORT with Init Duration; current handler does not log request path. |
| 2026-03-27T16:01:45Z | 4944.39 | 1508.51 | 6453.00 | 292 | CloudWatch REPORT with Init Duration; current handler does not log request path. |

## Interpretation

- Warm latency is measured externally from the deployed API endpoint after dedicated warm-up requests.
- Cold-start evidence is taken from CloudWatch `REPORT` log lines that include `Init Duration`.
- The current handler does not annotate request path in CloudWatch REPORT lines, so cold-start entries are treated as service-level evidence rather than route-specific labels.
