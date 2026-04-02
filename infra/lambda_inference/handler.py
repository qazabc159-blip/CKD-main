from __future__ import annotations

import base64
import json
import os
from typing import Any

from backend.service import (
    build_clinical_response,
    build_research_response,
    extract_inputs,
    health_payload,
)


CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": os.getenv("CKD_ALLOWED_ORIGIN", "*"),
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def json_response(status_code: int, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(payload),
    }


def get_method(event: dict[str, Any]) -> str:
    return (
        event.get("requestContext", {})
        .get("http", {})
        .get("method")
        or event.get("httpMethod")
        or "GET"
    ).upper()


def get_path(event: dict[str, Any]) -> str:
    path = event.get("rawPath") or event.get("path") or "/"
    stage = event.get("requestContext", {}).get("stage")
    if stage:
        stage_prefix = f"/{stage}"
        if path == stage_prefix:
            return "/"
        if path.startswith(stage_prefix + "/"):
            return path[len(stage_prefix) :]
    return path


def parse_event_body(event: dict[str, Any]) -> dict[str, Any]:
    raw_body = event.get("body")
    if raw_body in (None, ""):
        return {}

    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")

    if isinstance(raw_body, (bytes, bytearray)):
        raw_body = raw_body.decode("utf-8")

    if isinstance(raw_body, str):
        return json.loads(raw_body)

    if isinstance(raw_body, dict):
        return raw_body

    raise ValueError("Unsupported request body format.")


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    method = get_method(event)
    path = get_path(event)

    if method == "OPTIONS":
        return json_response(200, {"ok": True})

    if method == "GET" and path == "/health":
        return json_response(200, health_payload())

    if method != "POST":
        return json_response(405, {"detail": "Method not allowed."})

    try:
        payload = parse_event_body(event)
    except Exception as exc:
        return json_response(400, {"detail": f"Invalid JSON body: {exc}"})

    try:
        inputs = extract_inputs(payload)
    except ValueError as exc:
        return json_response(400, {"detail": str(exc)})

    mode = str(payload.get("mode", "research")).strip().lower()

    try:
        if path == "/predict/clinical":
            return json_response(200, build_clinical_response(inputs).to_dict())
        if path == "/predict/research":
            return json_response(200, build_research_response(inputs, "research").to_dict())
        if path == "/predict":
            if mode == "clinical":
                return json_response(200, build_clinical_response(inputs).to_dict())
            if mode == "research":
                return json_response(200, build_research_response(inputs, "research").to_dict())
            return json_response(400, {"detail": "Unsupported mode. Use `clinical` or `research`."})
    except Exception as exc:
        return json_response(
            500,
            {
                "detail": "Inference handler failed.",
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
            },
        )

    return json_response(404, {"detail": f"Route not found: {path}"})
