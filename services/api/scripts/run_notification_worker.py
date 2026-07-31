"""Run a bounded, content-free notification outbox batch.

The worker is disabled unless DR_AI_NOTIFICATION_WORKER_ENABLED is exactly
``true``. Provider delivery remains independently governed by the existing
external-delivery readiness gate.
"""

import argparse
import os

from app.config import get_settings
from app.database import SessionLocal
from app.notification_worker import process_one


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-items",
        type=int,
        default=100,
        help="Maximum outbox rows to process before exiting.",
    )
    args = parser.parse_args()
    if args.max_items < 1 or args.max_items > 10_000:
        raise SystemExit("--max-items must be between 1 and 10000")
    if os.environ.get("DR_AI_NOTIFICATION_WORKER_ENABLED", "").lower() != "true":
        raise SystemExit(
            "Notification worker is disabled. Set "
            "DR_AI_NOTIFICATION_WORKER_ENABLED=true on the explicitly approved target."
        )

    settings = get_settings()
    processed = 0
    with SessionLocal() as db:
        while processed < args.max_items and process_one(db, settings):
            processed += 1
    print(f"notification_worker_complete processed_count={processed}")


if __name__ == "__main__":
    main()
