from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = PROJECT_ROOT / "artifacts" / "model_registry" / "model_registry.json"
DEFAULT_EVENTS_PATH = PROJECT_ROOT / "artifacts" / "model_registry" / "registry_events.jsonl"
ALLOWED_STATUSES = {"candidate", "approved", "active", "retired"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Registry file does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events


def ensure_registry_shape(registry: dict[str, Any]) -> None:
    if "models" not in registry or not isinstance(registry["models"], list):
        raise RuntimeError("Registry must contain a `models` list.")
    for model in registry["models"]:
        status = model.get("status")
        if status not in ALLOWED_STATUSES:
            raise RuntimeError(f"Unsupported model status `{status}` in registry.")


def find_model(registry: dict[str, Any], model_id: str) -> dict[str, Any]:
    for model in registry.get("models", []):
        if model.get("model_id") == model_id:
            return model
    raise RuntimeError(f"Model `{model_id}` was not found in the registry.")


def current_active_model(registry: dict[str, Any]) -> dict[str, Any] | None:
    active_model_id = registry.get("active_model_id")
    if active_model_id:
        return find_model(registry, active_model_id)
    active_records = [model for model in registry.get("models", []) if model.get("status") == "active"]
    if len(active_records) == 1:
        return active_records[0]
    return None


def event_payload(event_type: str, actor: str, model_id: str, reason: str, **kwargs: Any) -> dict[str, Any]:
    timestamp = utc_now_iso()
    event = {
        "event_id": f"{timestamp}::{event_type}::{model_id}",
        "timestamp": timestamp,
        "event_type": event_type,
        "model_id": model_id,
        "actor": actor,
        "reason": reason,
    }
    event.update(kwargs)
    return event


def approve_model(registry: dict[str, Any], model_id: str, actor: str, note: str) -> tuple[dict[str, Any], dict[str, Any]]:
    ensure_registry_shape(registry)
    model = find_model(registry, model_id)
    if model.get("status") == "retired":
        raise RuntimeError("Retired models cannot be approved.")
    if model.get("status") == "active":
        raise RuntimeError("The active model is already approved through activation.")

    model["status"] = "approved"
    model["approved_by"] = actor
    model["approved_at"] = utc_now_iso()
    model["approval_note"] = note
    registry["updated_at"] = utc_now_iso()

    event = event_payload(
        "approved",
        actor=actor,
        model_id=model_id,
        reason=note,
        resulting_status="approved",
    )
    return registry, event


def promote_model(registry: dict[str, Any], model_id: str, actor: str, reason: str) -> tuple[dict[str, Any], dict[str, Any]]:
    ensure_registry_shape(registry)
    model = find_model(registry, model_id)
    current_active = current_active_model(registry)
    previous_active_id = current_active.get("model_id") if current_active else None

    if model.get("status") not in {"approved", "active"}:
        raise RuntimeError("Only approved models can be promoted to active.")

    if current_active and current_active.get("model_id") == model_id:
        raise RuntimeError(f"Model `{model_id}` is already active.")

    if current_active and current_active.get("status") == "active":
        current_active["status"] = "approved"

    if not model.get("approved_at"):
        model["approved_by"] = actor
        model["approved_at"] = utc_now_iso()
        model["approval_note"] = "Auto-approved during promotion."

    model["status"] = "active"
    model["last_promoted_by"] = actor
    model["last_promoted_at"] = utc_now_iso()
    model["promotion_note"] = reason
    registry["active_model_id"] = model_id
    registry["updated_at"] = utc_now_iso()

    event = event_payload(
        "promoted",
        actor=actor,
        model_id=model_id,
        reason=reason,
        previous_active_model_id=previous_active_id,
        new_active_model_id=model_id,
    )
    return registry, event


def resolve_rollback_target(registry: dict[str, Any], events: list[dict[str, Any]], target_model_id: str | None) -> str:
    if target_model_id:
        model = find_model(registry, target_model_id)
        if model.get("status") not in {"approved", "active"}:
            raise RuntimeError("Rollback target must currently be approved or active.")
        return target_model_id

    current_active = current_active_model(registry)
    current_active_id = current_active.get("model_id") if current_active else None
    for event in reversed(events):
        if event.get("event_type") not in {"promoted", "rolled_back"}:
            continue
        previous_id = event.get("previous_active_model_id")
        if previous_id and previous_id != current_active_id:
            candidate = find_model(registry, previous_id)
            if candidate.get("status") in {"approved", "active"}:
                return previous_id

    raise RuntimeError("No rollback target could be inferred. Provide --target-model-id explicitly.")


def rollback_model(
    registry: dict[str, Any],
    events: list[dict[str, Any]],
    actor: str,
    reason: str,
    target_model_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ensure_registry_shape(registry)
    current_active = current_active_model(registry)
    if current_active is None:
        raise RuntimeError("Registry has no active model to roll back from.")

    target_id = resolve_rollback_target(registry, events, target_model_id)
    if target_id == current_active.get("model_id"):
        raise RuntimeError("Rollback target matches the current active model.")

    target_model = find_model(registry, target_id)
    if current_active.get("status") == "active":
        current_active["status"] = "approved"

    target_model["status"] = "active"
    target_model["last_promoted_by"] = actor
    target_model["last_promoted_at"] = utc_now_iso()
    target_model["promotion_note"] = f"Rollback target: {reason}"
    registry["active_model_id"] = target_id
    registry["updated_at"] = utc_now_iso()

    event = event_payload(
        "rolled_back",
        actor=actor,
        model_id=target_id,
        reason=reason,
        previous_active_model_id=current_active.get("model_id"),
        new_active_model_id=target_id,
    )
    return registry, event
