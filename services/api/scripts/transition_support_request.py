"""Apply an attributable synthetic-stage support lifecycle transition."""

import argparse
import uuid

from app.config import get_settings
from app.database import SessionLocal
from app.support_operations import SupportTransitionError, transition_support_request


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument(
        "--action",
        required=True,
        choices=("start_review", "resolve", "mark_failed", "retry_queue"),
    )
    parser.add_argument("--expected-version", required=True, type=int)
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--actor-user-id", required=True, type=uuid.UUID)
    parser.add_argument(
        "--actor-kind",
        choices=("support_team", "system"),
        default="support_team",
    )
    args = parser.parse_args()

    settings = get_settings()
    if settings.environment == "production":
        raise SystemExit(
            "This operational command is disabled in production until a separate "
            "authorized support-operations boundary is approved."
        )

    with SessionLocal() as db:
        try:
            result = transition_support_request(
                db,
                public_reference=args.reference,
                action=args.action,
                expected_version=args.expected_version,
                idempotency_key=args.idempotency_key,
                actor_user_id=args.actor_user_id,
                actor_kind=args.actor_kind,
            )
        except SupportTransitionError as exc:
            db.rollback()
            raise SystemExit(f"Support transition rejected: {exc}") from exc

    replay_label = "replayed" if result.replayed else "applied"
    print(
        f"{replay_label}: request={result.support_request_id} "
        f"status={result.status} version={result.version}"
    )


if __name__ == "__main__":
    main()
