from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import KbPassage, KbRightsRecord, KbSource, KbSourceVersion


def provider_transmission_allowed(
    rights: KbRightsRecord,
    source: KbSource,
    *,
    now: datetime | None = None,
) -> bool:
    """Evaluate the live rights record; release manifests are never sufficient."""

    checked_at = now or datetime.now(UTC)
    return bool(
        rights.decision_status == "approved"
        and rights.model_provider_transmission_allowed
        and (rights.source_id is None or rights.source_id == source.id)
        and (rights.effective_at is None or rights.effective_at <= checked_at)
        and (rights.expires_at is None or rights.expires_at > checked_at)
    )


def assert_passages_provider_transmittable(
    db: Session,
    passage_ids: list[str],
    *,
    now: datetime | None = None,
) -> None:
    """Re-read and validate rights immediately before external transmission."""

    unique_ids = list(dict.fromkeys(passage_ids))
    if not unique_ids:
        return
    rows = db.execute(
        select(KbPassage.stable_id, KbSource, KbRightsRecord)
        .join(KbSourceVersion, KbSourceVersion.id == KbPassage.version_id)
        .join(KbSource, KbSource.id == KbSourceVersion.source_id)
        .join(KbRightsRecord, KbRightsRecord.id == KbSource.rights_record_id)
        .where(KbPassage.stable_id.in_(unique_ids))
    ).all()
    allowed_ids = {
        passage_id
        for passage_id, source, rights in rows
        if provider_transmission_allowed(rights, source, now=now)
    }
    if allowed_ids != set(unique_ids):
        raise PermissionError(
            "One or more evidence passages lack current provider-transmission rights."
        )
