"""Governed release activation and rollback controls for care references."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import (
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
)


class ReleaseActivationError(ValueError):
    pass


_ACCEPTED_SYNTHETIC_STAGE_STATES = {
    "not_required_for_early_synthetic_development",
    "product_owner_waived_for_current_stage",
}


def _validate_activation(
    release: GovernedCareRelease,
    *,
    on_date: date,
) -> None:
    required_review_types = frozenset(
        review_type
        for value in release.required_review_types_json
        if (review_type := str(value).strip())
    )
    if not required_review_types:
        raise ReleaseActivationError("required_review_contract_missing")
    if release.lifecycle_status not in {"reviewed", "active", "superseded"}:
        raise ReleaseActivationError("release_not_reviewed")
    synthetic_stage = release.provenance_json.get("data_class") == "wholly_synthetic"
    rights_ready = release.rights_status == "approved" or (
        synthetic_stage and release.rights_status in _ACCEPTED_SYNTHETIC_STAGE_STATES
    )
    if not rights_ready or not (
        release.storage_allowed and release.derivation_allowed
    ):
        raise ReleaseActivationError("release_rights_unavailable")
    if release.next_review_on is None or release.next_review_on < on_date:
        raise ReleaseActivationError("release_stale")
    if on_date < release.effective_from or (
        release.effective_to is not None and on_date > release.effective_to
    ):
        raise ReleaseActivationError("release_not_effective")
    approved_reviews = {
        review.review_type
        for review in release.reviews
        if (
            review.decision == "approved"
            or (synthetic_stage and review.decision in _ACCEPTED_SYNTHETIC_STAGE_STATES)
        )
        and review.reviewed_payload_checksum_sha256 == release.payload_checksum_sha256
    }
    if not required_review_types <= approved_reviews:
        raise ReleaseActivationError("required_reviews_missing")


def activate_release(
    session: Session,
    *,
    release: GovernedCareRelease,
    scope_key: str,
    actor_user_id: uuid.UUID | None,
    reason_code: str,
    on_date: date,
    rollback: bool = False,
    expected_version: str | None = None,
) -> GovernedCareReleaseActivation:
    """Move an active pointer and append evidence; never mutate release content."""

    session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {
            "key": (
                f"care-reference-release:{release.release_type}:"
                f"{release.release_key}:{scope_key}"
            )
        },
    )
    if expected_version is not None and release.version != expected_version:
        raise ReleaseActivationError("expected_version_conflict")
    _validate_activation(
        release,
        on_date=on_date,
    )
    active = session.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == release.release_type,
            GovernedActiveCareRelease.release_key == release.release_key,
            GovernedActiveCareRelease.scope_key == scope_key,
        )
    )
    if active is not None and active.release_id == release.id:
        raise ReleaseActivationError("release_already_active")

    prior_release_id = active.release_id if active is not None else None
    action = "rollback" if rollback else ("supersede" if active is not None else "activate")
    event = GovernedCareReleaseActivation(
        release_id=release.id,
        release_type=release.release_type,
        release_key=release.release_key,
        scope_key=scope_key,
        action=action,
        prior_release_id=prior_release_id,
        actor_user_id=actor_user_id,
        reason_code=reason_code,
    )
    session.add(event)
    session.flush()
    if active is None:
        active = GovernedActiveCareRelease(
            release_type=release.release_type,
            release_key=release.release_key,
            scope_key=scope_key,
            release_id=release.id,
            activation_event_id=event.id,
        )
        session.add(active)
    else:
        active.release_id = release.id
        active.activation_event_id = event.id
    session.flush()
    return event
