# CloudWatch screenshot guidance for Chapter 5.5

Dashboard URL:
- https://ap-northeast-1.console.aws.amazon.com/cloudwatch/home?region=ap-northeast-1#dashboards:name=CKD-Inference-Operational-Dashboard

## Best dashboard panels to capture

### 1. Lambda duration (p50 / p95 / max)
Why it matters:
- This is the clearest system-level latency figure.
- It supports discussion of warm inference performance and occasional cold-start overhead.

Suggested caption angle:
- `CloudWatch metrics showing Lambda duration percentiles for the CKD inference service.`

### 2. API latency vs integration latency (p50 / p95)
Why it matters:
- This shows end-to-end API latency and the portion attributable to integration execution.
- It helps explain the difference between client-observed latency and backend-only runtime.

Suggested caption angle:
- `CloudWatch metrics comparing API Gateway latency and integration latency for the deployed inference route.`

### 3. API Gateway request volume and errors
Why it matters:
- This demonstrates that the endpoint is being exercised and gives a simple reliability view.
- It is especially useful if 4xx/5xx remain near zero.

Suggested caption angle:
- `CloudWatch metrics summarizing request volume and API error counts for the deployed HTTP API stage.`

### 4. Route-level request counts and latency (access logs)
Why it matters:
- This is the most thesis-friendly panel if you want proof that different routes such as `/predict/research`, `/predict/clinical`, and `/health` were actually hit.
- It compensates for the fact that default API Gateway metrics are stage-level rather than route-level.

Suggested caption angle:
- `Route-level access-log aggregation showing requests and average latency for the deployed HTTP API routes.`

### 5. Recent API access logs or recent Lambda logs
Why it matters:
- Use one log-focused screenshot if you want very concrete implementation evidence.
- Good for appendices or a short figure in 5.5.

## Screenshot order I recommend
1. Public app with live response
2. Lambda duration panel
3. API latency vs integration latency panel
4. Route-level access-log panel

## Practical capture tips
- Set the dashboard time range to a recent window that definitely includes your test traffic.
- Trigger a few fresh research and clinical requests immediately before capturing.
- Prefer panels with visible non-zero values and low clutter.
- Keep the dashboard in light mode if you want maximum readability inside the thesis PDF.
