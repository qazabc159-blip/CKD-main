from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_registry_ops import (
    DEFAULT_EVENTS_PATH,
    DEFAULT_REGISTRY_PATH,
    append_event,
    approve_model,
    load_registry,
    write_registry,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Approve a candidate model in the CKD model registry.")
    parser.add_argument("--model-id", required=True, help="Model identifier to approve.")
    parser.add_argument("--actor", required=True, help="Actor recorded in the approval event.")
    parser.add_argument("--note", required=True, help="Approval note stored in the registry and event log.")
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH), help="Path to model_registry.json.")
    parser.add_argument("--events-path", default=str(DEFAULT_EVENTS_PATH), help="Path to registry_events.jsonl.")
    args = parser.parse_args()

    registry_path = Path(args.registry_path).expanduser().resolve()
    events_path = Path(args.events_path).expanduser().resolve()
    registry = load_registry(registry_path)
    registry, event = approve_model(registry, args.model_id, args.actor, args.note)
    write_registry(registry_path, registry)
    append_event(events_path, event)

    print(
        json.dumps(
            {
                "status": "ok",
                "action": "approve",
                "model_id": args.model_id,
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
