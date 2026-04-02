from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_registry_ops import (
    DEFAULT_EVENTS_PATH,
    DEFAULT_REGISTRY_PATH,
    append_event,
    load_events,
    load_registry,
    rollback_model,
    write_registry,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Roll back the CKD model registry to a previous approved model.")
    parser.add_argument("--actor", required=True, help="Actor recorded in the rollback event.")
    parser.add_argument("--reason", required=True, help="Rollback reason stored in the event log.")
    parser.add_argument("--target-model-id", default="", help="Optional explicit rollback target model identifier.")
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH), help="Path to model_registry.json.")
    parser.add_argument("--events-path", default=str(DEFAULT_EVENTS_PATH), help="Path to registry_events.jsonl.")
    args = parser.parse_args()

    registry_path = Path(args.registry_path).expanduser().resolve()
    events_path = Path(args.events_path).expanduser().resolve()
    registry = load_registry(registry_path)
    events = load_events(events_path)
    registry, event = rollback_model(
        registry,
        events=events,
        actor=args.actor,
        reason=args.reason,
        target_model_id=args.target_model_id or None,
    )
    write_registry(registry_path, registry)
    append_event(events_path, event)

    print(
        json.dumps(
            {
                "status": "ok",
                "action": "rollback",
                "active_model_id": registry.get("active_model_id"),
                "registry_path": str(registry_path),
                "events_path": str(events_path),
                "event": event,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
