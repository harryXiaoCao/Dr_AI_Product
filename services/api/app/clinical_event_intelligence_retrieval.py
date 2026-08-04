"""Server-directed, release-bound retrieval for Clinical Event Intelligence."""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinical_event_intelligence_contracts import (
    FrozenClinicalEventSnapshot,
    RetrievalManifest,
    RetrievalSource,
    canonical_checksum,
)
from app.models import (
    GovernedActiveCareRelease,
    GovernedCareRelease,
    PricingReferenceItem,
)

RETRIEVAL_CONTRACT_VERSION = "clinical-event-intelligence-retrieval.v1"

_TYPE_MAP = {
    "pricing_reference": "regional_reference",
    "facility_pricing_reference": "facility_price",
    "payer_pricing_reference": "payer_price",
    "code_catalog": "code_catalog",
    "clinical_guideline": "guideline",
    "care_plan": "care_pathway",
    "payer_policy": "payer_policy",
    "comparable_case_set": "comparable_case",
}

_CHECKSUM = re.compile(r"^[0-9a-f]{64}$")
_DENIED_RIGHTS = {"unresolved", "denied", "expired", "withdrawn"}


def _release_is_provider_admissible(
    pointer: GovernedActiveCareRelease,
    release: GovernedCareRelease,
) -> bool:
    """Fail closed unless the active pointer and immutable release agree."""

    return (
        pointer.release_type == release.release_type
        and pointer.release_key == release.release_key
        and release.lifecycle_status in {"reviewed", "active"}
        and release.rights_status not in _DENIED_RIGHTS
        and release.storage_allowed
        and release.derivation_allowed
        and release.provider_transmission_allowed
        and bool(_CHECKSUM.fullmatch(release.source_checksum_sha256))
        and bool(_CHECKSUM.fullmatch(release.payload_checksum_sha256))
    )


def _cost_analogues(release: GovernedCareRelease) -> list[dict[str, object]]:
    """Expose only structured, non-confidential analogue fields."""

    raw = release.provenance_json.get("cost_analogues")
    if not isinstance(raw, list):
        return []
    allowed = {
        "code_system",
        "service_code",
        "unit",
        "currency",
        "amount_low_minor",
        "amount_high_minor",
        "comparability",
    }
    values: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict) or item.get("confidential") is True:
            continue
        safe = {key: value for key, value in item.items() if key in allowed}
        if (
            isinstance(safe.get("amount_low_minor"), int)
            and isinstance(safe.get("amount_high_minor"), int)
            and safe["amount_low_minor"] >= 0
            and safe["amount_high_minor"] >= safe["amount_low_minor"]
        ):
            values.append(safe)
    return values


def _source_checksum(release: GovernedCareRelease, payload: dict[str, object]) -> str:
    return canonical_checksum(
        {
            "release_id": str(release.id),
            "release_version": release.version,
            "payload_checksum_sha256": release.payload_checksum_sha256,
            "payload": payload,
        }
    )


def retrieve_authorized_intelligence_sources(
    db: Session,
    *,
    snapshot: FrozenClinicalEventSnapshot,
    payer_organization_id: str,
) -> RetrievalManifest:
    """Select only active, applicable, provider-transmittable governed releases."""

    location = snapshot.location
    authorization_scope = {
        "payer_request_id": snapshot.payer_request_id,
        "payer_organization_id": payer_organization_id,
        "jurisdiction_code": location.jurisdiction_code,
        "province_code": location.province_code,
        "city_code": location.city_code,
        "facility_level": location.facility_level,
        "hospital_id": location.hospital_id,
        "clinic_id": location.clinic_id,
    }
    rows = db.execute(
        select(GovernedActiveCareRelease, GovernedCareRelease)
        .join(
            GovernedCareRelease,
            GovernedCareRelease.id == GovernedActiveCareRelease.release_id,
        )
        .where(GovernedCareRelease.release_type.in_(tuple(_TYPE_MAP)))
        .order_by(GovernedCareRelease.release_type, GovernedCareRelease.release_key)
    ).all()
    sources: list[RetrievalSource] = []
    requested_codes = {line.service_code for line in snapshot.requested_lines}
    reference_date = min(date.fromisoformat(line.service_date) for line in snapshot.requested_lines)
    for pointer, release in rows:
        if not _release_is_provider_admissible(pointer, release):
            continue
        if location.jurisdiction_code and release.jurisdiction != location.jurisdiction_code:
            continue
        if release.effective_from > reference_date or (
            release.effective_to is not None and release.effective_to < reference_date
        ):
            continue
        facility_scope = release.facility_scope_json or {}
        allowed_levels = facility_scope.get("facility_levels")
        if (
            isinstance(allowed_levels, list)
            and location.facility_level
            and location.facility_level not in allowed_levels
        ):
            continue
        if release.release_type in {"payer_pricing_reference", "payer_policy"}:
            payer_ids = facility_scope.get("payer_organization_ids")
            if not isinstance(payer_ids, list) or payer_organization_id not in payer_ids:
                continue
        if release.release_type == "facility_pricing_reference":
            hospital_ids = facility_scope.get("hospital_ids")
            clinic_ids = facility_scope.get("clinic_ids")
            hospital_match = isinstance(hospital_ids, list) and location.hospital_id in hospital_ids
            clinic_match = isinstance(clinic_ids, list) and location.clinic_id in clinic_ids
            if not hospital_match and not clinic_match:
                continue
        payload: dict[str, object] = {
            "release_key": release.release_key,
            "scope_key": pointer.scope_key,
            "jurisdiction": release.jurisdiction,
            "region": release.region,
            "currency": release.currency,
            "effective_from": str(release.effective_from),
            "effective_to": str(release.effective_to) if release.effective_to else None,
            "facility_scope": facility_scope,
        }
        if release.release_type in {
            "pricing_reference",
            "facility_pricing_reference",
            "payer_pricing_reference",
        }:
            price_rows = db.scalars(
                select(PricingReferenceItem)
                .where(
                    PricingReferenceItem.pricing_reference_release_id == release.id,
                    PricingReferenceItem.service_code.in_(requested_codes),
                    PricingReferenceItem.confidential.is_(False),
                )
                .order_by(PricingReferenceItem.service_code, PricingReferenceItem.id)
            ).all()
            payload["price_items"] = [
                {
                    "source_item_id": str(item.id),
                    "code_system": item.code_system,
                    "service_code": item.service_code,
                    "unit": item.unit,
                    "currency": item.currency,
                    "amount_low_minor": item.amount_low_minor,
                    "amount_high_minor": item.amount_high_minor,
                    "facility_scope_key": item.facility_scope_key,
                }
                for item in price_rows
            ]
            if not price_rows:
                continue
        elif release.release_type in {"care_plan", "comparable_case_set"}:
            analogues = _cost_analogues(release)
            if analogues:
                payload["cost_analogues"] = analogues
        sources.append(
            RetrievalSource(
                source_id=f"release:{release.id}",
                source_type=_TYPE_MAP[release.release_type],  # type: ignore[arg-type]
                release_id=str(release.id),
                release_version=release.version,
                checksum_sha256=_source_checksum(release, payload),
                authority=release.source_authority,
                provider_transmission_allowed=True,
                payload=payload,
            )
        )
    present = {source.source_type for source in sources}
    expected = {
        "regional_reference",
        "code_catalog",
        "guideline",
        "care_pathway",
        "payer_policy",
        "comparable_case",
    }
    payload = {
        "retrieval_contract_version": RETRIEVAL_CONTRACT_VERSION,
        "authorization_scope_checksum_sha256": canonical_checksum(authorization_scope),
        "sources": [source.model_dump(mode="json") for source in sources],
        "missing_source_types": sorted(expected - present),
    }
    return RetrievalManifest(
        **payload,
        manifest_checksum_sha256=canonical_checksum(payload),
    )
