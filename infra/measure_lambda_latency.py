from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import boto3
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "artifacts" / "system_eval_aws"
DEFAULT_STACK_NAME = "ckd-inference-stack"
DEFAULT_REGION = "ap-northeast-1"


RESEARCH_PAYLOAD = {
    "mode": "research",
    "inputs": {
        "age": 55,
        "sg": 1.02,
        "al": 2,
        "su": 0,
        "rbc": "normal",
        "pc": "abnormal",
        "pcc": "notpresent",
        "ba": "notpresent",
        "appet": "good",
        "pe": "no",
        "ane": "no",
        "bgr": 148,
        "bu": 44,
        "sc": 1.6,
        "sod": 137,
        "pot": 4.5,
        "hemo": 12.4,
        "pcv": 38,
        "wbcc": 7800,
        "rbcc": 4.5,
        "htn": "yes",
        "dm": "yes",
        "cad": "no",
    },
    "context": {
        "case_id": "LATENCY-RESEARCH-0001",
        "patient_name": "Latency Research Probe",
        "clinical_note": "Automated warm-latency measurement for the AWS research route.",
    },
}

CLINICAL_PAYLOAD = {
    "mode": "clinical",
    "inputs": {
        "age": 55,
        "sex": "male",
        "sbp": 130,
        "dbp": 80,
        "bmi": 24.5,
        "egfr": 65,
        "uacr": 30,
        "hba1c": 7.2,
        "scr": 1.2,
        "potassium": 4.2,
        "dm": "yes",
        "htn": "yes",
        "cvd": "no",
        "proteinuria_flag": "yes",
    },
    "context": {
        "case_id": "LATENCY-CLINICAL-0001",
        "patient_name": "Latency Clinical Probe",
        "clinical_note": "Automated warm-latency measurement for the AWS clinical route.",
    },
}


REPORT_PATTERN = re.compile(
    r"REPORT RequestId: (?P<request_id>[^\t]+)\t"
    r"Duration: (?P<duration_ms>[0-9.]+) ms\t"
    r"Billed Duration: (?P<billed_duration_ms>[0-9.]+) ms\t"
    r"Memory Size: (?P<memory_size_mb>[0-9.]+) MB\t"
    r"Max Memory Used: (?P<max_memory_used_mb>[0-9.]+) MB\t"
    r"(?:Init Duration: (?P<init_duration_ms>[0-9.]+) ms\t)?"
)


@dataclass
class RouteSample:
    route_name: str
    phase: str
    iteration: int
    timestamp_utc: str
    elapsed_ms: float
    status_code: int | None
    ok: bool
    risk_score: float | None
    prediction_label: str | None
    model_version: str | None
    serving_route: str | None
    error: str | None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(sorted_values[lower])
    lower_value = sorted_values[lower]
    upper_value = sorted_values[upper]
    weight = index - lower
    return float(lower_value + (upper_value - lower_value) * weight)


def summarize_samples(samples: list[RouteSample]) -> dict[str, Any]:
    successful = [sample.elapsed_ms for sample in samples if sample.ok and sample.status_code == 200]
    return {
        "n_total": len(samples),
        "n_success": sum(1 for sample in samples if sample.ok and sample.status_code == 200),
        "n_failure": sum(1 for sample in samples if not sample.ok or sample.status_code != 200),
        "mean_ms": round(statistics.mean(successful), 2) if successful else None,
        "median_ms": round(statistics.median(successful), 2) if successful else None,
        "p50_ms": round(percentile(successful, 0.50), 2) if successful else None,
        "p95_ms": round(percentile(successful, 0.95), 2) if successful else None,
        "p99_ms": round(percentile(successful, 0.99), 2) if successful else None,
        "min_ms": round(min(successful), 2) if successful else None,
        "max_ms": round(max(successful), 2) if successful else None,
    }


def call_endpoint(
    session: requests.Session,
    url: str,
    payload: dict[str, Any],
    route_name: str,
    phase: str,
    iteration: int,
    timeout_seconds: int,
) -> RouteSample:
    started_at = time.perf_counter()
    status_code: int | None = None
    response_payload: dict[str, Any] | None = None
    error: str | None = None

    try:
        response = session.post(url, json=payload, timeout=timeout_seconds)
        status_code = response.status_code
        response.raise_for_status()
        response_payload = response.json()
    except Exception as exc:  # noqa: BLE001
        error = str(exc)

    elapsed_ms = (time.perf_counter() - started_at) * 1000.0
    return RouteSample(
        route_name=route_name,
        phase=phase,
        iteration=iteration,
        timestamp_utc=utc_now_iso(),
        elapsed_ms=round(elapsed_ms, 2),
        status_code=status_code,
        ok=error is None,
        risk_score=response_payload.get("risk_score") if response_payload else None,
        prediction_label=response_payload.get("prediction_label") if response_payload else None,
        model_version=response_payload.get("model_version") if response_payload else None,
        serving_route=response_payload.get("serving_route") if response_payload else None,
        error=error,
    )


def measure_route(
    session: requests.Session,
    base_url: str,
    route_path: str,
    route_name: str,
    payload: dict[str, Any],
    warmup_runs: int,
    measured_runs: int,
    timeout_seconds: int,
) -> list[RouteSample]:
    samples: list[RouteSample] = []
    full_url = base_url.rstrip("/") + route_path

    for iteration in range(1, warmup_runs + 1):
        samples.append(
            call_endpoint(
                session=session,
                url=full_url,
                payload=payload,
                route_name=route_name,
                phase="warmup",
                iteration=iteration,
                timeout_seconds=timeout_seconds,
            )
        )

    for iteration in range(1, measured_runs + 1):
        samples.append(
            call_endpoint(
                session=session,
                url=full_url,
                payload=payload,
                route_name=route_name,
                phase="measured",
                iteration=iteration,
                timeout_seconds=timeout_seconds,
            )
        )

    return samples


def get_stack_base_url(cloudformation_client: Any, stack_name: str) -> str:
    stacks = cloudformation_client.describe_stacks(StackName=stack_name)["Stacks"]
    outputs = {item["OutputKey"]: item["OutputValue"] for item in stacks[0].get("Outputs", [])}
    base_url = outputs.get("HttpApiBaseUrl")
    if not base_url:
        raise RuntimeError(f"Stack `{stack_name}` does not expose HttpApiBaseUrl.")
    return base_url


def get_lambda_name(cloudformation_client: Any, stack_name: str) -> str:
    resources = cloudformation_client.describe_stack_resources(StackName=stack_name)["StackResources"]
    for resource in resources:
        if resource["ResourceType"] == "AWS::Lambda::Function" and resource["LogicalResourceId"] == "CkdInferenceFunction":
            return resource["PhysicalResourceId"]
    raise RuntimeError(f"Could not resolve Lambda function name from stack `{stack_name}`.")


def fetch_recent_cold_reports(
    logs_client: Any,
    log_group_name: str,
    lookback_hours: int,
    max_items: int = 5,
) -> list[dict[str, Any]]:
    start_time_ms = int((datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).timestamp() * 1000)
    paginator = logs_client.get_paginator("filter_log_events")
    collected: list[dict[str, Any]] = []

    for page in paginator.paginate(logGroupName=log_group_name, startTime=start_time_ms):
        for event in page.get("events", []):
            message = event.get("message", "")
            if not message.startswith("REPORT RequestId:"):
                continue
            if "Init Duration:" not in message:
                continue

            match = REPORT_PATTERN.search(message)
            if not match:
                continue

            parsed = match.groupdict()
            collected.append(
                {
                    "timestamp_utc": datetime.fromtimestamp(event["timestamp"] / 1000, tz=timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "log_stream_name": event.get("logStreamName"),
                    "request_id": parsed["request_id"],
                    "duration_ms": float(parsed["duration_ms"]),
                    "billed_duration_ms": float(parsed["billed_duration_ms"]),
                    "memory_size_mb": float(parsed["memory_size_mb"]),
                    "max_memory_used_mb": float(parsed["max_memory_used_mb"]),
                    "init_duration_ms": float(parsed["init_duration_ms"]) if parsed.get("init_duration_ms") else None,
                    "route_note": "CloudWatch REPORT with Init Duration; current handler does not log request path.",
                }
            )

    collected.sort(key=lambda item: item["timestamp_utc"], reverse=True)
    return collected[:max_items]


def write_samples_csv(output_path: Path, samples: list[RouteSample]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(samples[0]).keys()) if samples else [])
        if samples:
            writer.writeheader()
            for sample in samples:
                writer.writerow(asdict(sample))


def write_json(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_summary_markdown(
    output_path: Path,
    *,
    base_url: str,
    lambda_name: str,
    measured_runs: int,
    warmup_runs: int,
    route_summaries: dict[str, dict[str, Any]],
    cold_reports: list[dict[str, Any]],
) -> None:
    lines = [
        "# AWS Inference Latency Summary",
        "",
        f"- Generated at: `{utc_now_iso()}`",
        f"- Base URL: `{base_url}`",
        f"- Lambda function: `{lambda_name}`",
        f"- Warm-up runs per route: `{warmup_runs}`",
        f"- Measured warm runs per route: `{measured_runs}`",
        "",
        "## Warm Latency",
        "",
        "| Route | Mean (ms) | Median (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Min (ms) | Max (ms) | Success / Total |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for route_name, summary in route_summaries.items():
        lines.append(
            f"| {route_name} | {summary['mean_ms']} | {summary['median_ms']} | {summary['p50_ms']} | "
            f"{summary['p95_ms']} | {summary['p99_ms']} | {summary['min_ms']} | {summary['max_ms']} | "
            f"{summary['n_success']} / {summary['n_total']} |"
        )

    lines.extend(["", "## Recent Cold-Start Evidence from CloudWatch", ""])

    if cold_reports:
        lines.extend(
            [
                "| Timestamp (UTC) | Duration (ms) | Init Duration (ms) | Billed (ms) | Max Memory (MB) | Note |",
                "|---|---:|---:|---:|---:|---|",
            ]
        )
        for item in cold_reports:
            lines.append(
                f"| {item['timestamp_utc']} | {item['duration_ms']:.2f} | {item['init_duration_ms']:.2f} | "
                f"{item['billed_duration_ms']:.2f} | {item['max_memory_used_mb']:.0f} | {item['route_note']} |"
            )
    else:
        lines.append("No recent CloudWatch REPORT entries with `Init Duration` were found in the requested lookback window.")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Warm latency is measured externally from the deployed API endpoint after dedicated warm-up requests.",
            "- Cold-start evidence is taken from CloudWatch `REPORT` log lines that include `Init Duration`.",
            "- The current handler does not annotate request path in CloudWatch REPORT lines, so cold-start entries are treated as service-level evidence rather than route-specific labels.",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure AWS Lambda/API Gateway latency for the CKD inference service.")
    parser.add_argument("--stack-name", default=DEFAULT_STACK_NAME, help="CloudFormation stack name.")
    parser.add_argument("--region", default=DEFAULT_REGION, help="AWS region.")
    parser.add_argument("--base-url", default="", help="Optional override for the deployed API base URL.")
    parser.add_argument("--warmup-runs", type=int, default=2, help="Number of warm-up requests per route.")
    parser.add_argument("--measured-runs", type=int, default=20, help="Number of measured warm requests per route.")
    parser.add_argument("--timeout-seconds", type=int, default=60, help="HTTP timeout per request.")
    parser.add_argument("--cold-lookback-hours", type=int, default=24, help="How far back to search CloudWatch for cold-start evidence.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for CSV/JSON/Markdown outputs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    session = boto3.Session(region_name=args.region)
    cloudformation = session.client("cloudformation")
    logs = session.client("logs")
    http_session = requests.Session()

    base_url = args.base_url or get_stack_base_url(cloudformation, args.stack_name)
    lambda_name = get_lambda_name(cloudformation, args.stack_name)
    log_group_name = f"/aws/lambda/{lambda_name}"

    research_samples = measure_route(
        session=http_session,
        base_url=base_url,
        route_path="/predict/research",
        route_name="research",
        payload=RESEARCH_PAYLOAD,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
        timeout_seconds=args.timeout_seconds,
    )
    clinical_samples = measure_route(
        session=http_session,
        base_url=base_url,
        route_path="/predict/clinical",
        route_name="clinical",
        payload=CLINICAL_PAYLOAD,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
        timeout_seconds=args.timeout_seconds,
    )

    all_samples = research_samples + clinical_samples
    measured_only = {
        "research": [sample for sample in research_samples if sample.phase == "measured"],
        "clinical": [sample for sample in clinical_samples if sample.phase == "measured"],
    }
    route_summaries = {route_name: summarize_samples(samples) for route_name, samples in measured_only.items()}
    cold_reports = fetch_recent_cold_reports(logs, log_group_name, lookback_hours=args.cold_lookback_hours)

    write_samples_csv(output_dir / "lambda_latency_samples.csv", all_samples)
    write_json(
        output_dir / "lambda_latency_summary.json",
        {
            "generated_at": utc_now_iso(),
            "base_url": base_url,
            "lambda_function": lambda_name,
            "log_group_name": log_group_name,
            "warmup_runs": args.warmup_runs,
            "measured_runs": args.measured_runs,
            "route_summaries": route_summaries,
            "recent_cold_reports": cold_reports,
        },
    )
    write_summary_markdown(
        output_dir / "lambda_latency_summary.md",
        base_url=base_url,
        lambda_name=lambda_name,
        measured_runs=args.measured_runs,
        warmup_runs=args.warmup_runs,
        route_summaries=route_summaries,
        cold_reports=cold_reports,
    )

    print(f"Latency outputs written to: {output_dir}")
    print(json.dumps(route_summaries, indent=2, ensure_ascii=False))
    if cold_reports:
        print("Recent cold-start evidence:")
        print(json.dumps(cold_reports[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
