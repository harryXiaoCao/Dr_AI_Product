"""Idempotent local-only fixture for the CEI three-role workflow."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinical_event_intelligence_contracts import canonical_checksum
from app.config import Settings
from app.models import (
    CareRelationship,
    Clinic,
    ClinicalEvent,
    DoctorProfile,
    GovernedActiveCareRelease,
    GovernedCareRelease,
    GovernedCareReleaseActivation,
    GovernedCareReleaseReview,
    Hospital,
    PatientProfile,
    PayerMembership,
    PayerOrganization,
    PayerRequest,
    PayerRequestLine,
    PricingReferenceItem,
    PricingReferenceSet,
    User,
    UserRole,
)
from app.security import hash_password, verify_password

FIXTURE_KEY = "clinical-event-intelligence-local-synthetic-v1"
DOCTOR_EMAIL = "cei.doctor.local@example.com"
PATIENT_EMAIL = "cei.patient.local@example.com"
PAYER_EMAIL = "cei.payer.local@example.com"
LOCAL_ONLY_PASSWORD = "CEI-Local-Synthetic-2026!"
PRICE_RELEASE_KEY = "clinical-event-intelligence-local-synthetic-price"


@dataclass(frozen=True)
class SyntheticClinicalEventIntelligenceResult:
    payer_request_id: uuid.UUID
    doctor_route: str
    patient_route: str
    payer_route: str


def _user(db: Session, *, email: str, role: UserRole, phone: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            phone_number=phone,
            password_hash=hash_password(LOCAL_ONLY_PASSWORD),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()
    elif user.role != role:
        raise RuntimeError(f"cei_fixture_role_conflict:{email}")
    else:
        user.is_active = True
        if not verify_password(LOCAL_ONLY_PASSWORD, user.password_hash):
            user.password_hash = hash_password(LOCAL_ONLY_PASSWORD)
    return user


def _accounts(
    db: Session,
) -> tuple[User, DoctorProfile, PatientProfile, PayerMembership]:
    doctor_user = _user(db, email=DOCTOR_EMAIL, role=UserRole.doctor, phone="+8613900005101")
    patient_user = _user(db, email=PATIENT_EMAIL, role=UserRole.patient, phone="+8613900005102")
    payer_user = _user(db, email=PAYER_EMAIL, role=UserRole.payer, phone="+8613900005103")
    doctor = db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == doctor_user.id))
    if doctor is None:
        doctor = DoctorProfile(
            user_id=doctor_user.id,
            display_name="Dr. CEI Synthetic",
            title="Synthetic Clinical Reviewer",
            hospital_name="CEI Synthetic Hospital",
            specialty="Rehabilitation medicine",
            preferred_language="zh-Hans",
        )
        db.add(doctor)
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == patient_user.id))
    if patient is None:
        patient = PatientProfile(
            user_id=patient_user.id,
            display_name="CEI Synthetic Patient",
            synthetic_identifier="SYN-CEI-LOCAL-001",
            preferred_language="zh-Hans",
            medical_history_setup_completed=True,
        )
        db.add(patient)
    organization = db.scalar(
        select(PayerOrganization).where(PayerOrganization.name == "CEI Synthetic Municipal Payer")
    )
    if organization is None:
        organization = PayerOrganization(
            name="CEI Synthetic Municipal Payer",
            organization_type="public_payer",
            jurisdiction_code="CN",
            verification_status="synthetic_only",
        )
        db.add(organization)
    db.flush()
    membership = db.scalar(
        select(PayerMembership).where(
            PayerMembership.user_id == payer_user.id,
            PayerMembership.payer_organization_id == organization.id,
        )
    )
    if membership is None:
        membership = PayerMembership(
            user_id=payer_user.id,
            payer_organization_id=organization.id,
            display_name="CEI Synthetic Payer Reviewer",
            title="Synthetic expenditure reviewer",
            status="active",
            scope="synthetic_review",
        )
        db.add(membership)
    else:
        membership.status = "active"
        membership.scope = "synthetic_review"
    relationship = db.scalar(
        select(CareRelationship).where(
            CareRelationship.doctor_id == doctor.id,
            CareRelationship.patient_id == patient.id,
        )
    )
    if relationship is None:
        now = datetime.now(UTC)
        db.add(
            CareRelationship(
                doctor_id=doctor.id,
                patient_id=patient.id,
                is_active=True,
                status="active",
                can_review_recovery_plans=True,
                requested_at=now,
                responded_at=now,
                approved_at=now,
            )
        )
    else:
        relationship.is_active = True
        relationship.status = "active"
        relationship.can_review_recovery_plans = True
        relationship.responded_at = relationship.responded_at or relationship.created_at
        relationship.approved_at = relationship.approved_at or relationship.created_at
        relationship.revoked_at = None
    db.flush()
    return doctor_user, doctor, patient, membership


def _facility(db: Session) -> tuple[Hospital, Clinic]:
    hospital = db.scalar(select(Hospital).where(Hospital.organization_code == "SYN-CEI-H001"))
    if hospital is None:
        hospital = Hospital(
            name="CEI Synthetic Hospital",
            legal_name="CEI Synthetic Hospital Local Fixture",
            organization_code="SYN-CEI-H001",
            jurisdiction_code="CN",
            country_code="CN",
            province="CN-SYN",
            city="CN-SYN-001",
            status="active",
            metadata_json={"data_class": "wholly_synthetic", "fixture_key": FIXTURE_KEY},
        )
        db.add(hospital)
        db.flush()
    clinic = db.scalar(
        select(Clinic).where(
            Clinic.hospital_id == hospital.id,
            Clinic.facility_code == "SYN-CEI-C001",
        )
    )
    if clinic is None:
        clinic = Clinic(
            hospital_id=hospital.id,
            name="CEI Synthetic Rehabilitation Clinic",
            facility_code="SYN-CEI-C001",
            facility_level="synthetic_tertiary",
            department_code="SYN-REHAB",
            timezone="Asia/Shanghai",
            status="active",
            metadata_json={"data_class": "wholly_synthetic", "fixture_key": FIXTURE_KEY},
        )
        db.add(clinic)
        db.flush()
    return hospital, clinic


def _price_release(db: Session, *, payer_organization_id: uuid.UUID) -> None:
    version = "2026-08-02.v1"
    source_payload = {
        "fixture_key": FIXTURE_KEY,
        "code_system": "DR-AI-SYNTHETIC",
        "service_code": "SYN-CEI-LAB-001",
        "unit": "panel",
        "currency": "CNY",
        "amount_low_minor": 8000,
        "amount_high_minor": 12000,
    }
    checksum = canonical_checksum(source_payload)
    release = db.scalar(
        select(GovernedCareRelease).where(
            GovernedCareRelease.release_type == "payer_pricing_reference",
            GovernedCareRelease.release_key == PRICE_RELEASE_KEY,
            GovernedCareRelease.version == version,
        )
    )
    if release is None:
        release = GovernedCareRelease(
            release_type="payer_pricing_reference",
            release_key=PRICE_RELEASE_KEY,
            version=version,
            schema_version="pricing-reference.v1",
            lifecycle_status="reviewed",
            jurisdiction="CN",
            region="CN-SYN",
            facility_scope_json={
                "payer_organization_ids": [str(payer_organization_id)],
                "facility_levels": ["synthetic_tertiary"],
                "stage": "controlled_synthetic_staging",
            },
            currency="CNY",
            effective_from=date(2026, 1, 1),
            effective_to=date(2027, 12, 31),
            source_authority="Dr. AI wholly synthetic local fixture",
            source_locator=f"urn:dr-ai:synthetic:{FIXTURE_KEY}:price",
            retrieved_at=datetime(2026, 8, 2, tzinfo=UTC),
            source_checksum_sha256=checksum,
            payload_checksum_sha256=checksum,
            provenance_json={"data_class": "wholly_synthetic", "fixture_key": FIXTURE_KEY},
            required_review_types_json=["synthetic_stage"],
            rights_status="product_owner_waived_for_current_stage",
            storage_allowed=True,
            derivation_allowed=True,
            redistribution_allowed=False,
            provider_transmission_allowed=True,
            last_verified_on=date(2026, 8, 2),
            next_review_on=date(2027, 8, 2),
        )
        db.add(release)
        db.flush()
        db.add(
            GovernedCareReleaseReview(
                release_id=release.id,
                review_type="synthetic_stage",
                decision="product_owner_waived_for_current_stage",
                reviewer_name="Dr. AI synthetic-stage product policy",
                reviewed_payload_checksum_sha256=checksum,
                rationale="Wholly synthetic local development only.",
            )
        )
        db.add(
            PricingReferenceSet(
                release_id=release.id,
                price_type="range",
                amount_semantics="service_date",
                comparability="exact",
            )
        )
        db.flush()
        db.add(
            PricingReferenceItem(
                pricing_reference_release_id=release.id,
                code_system="DR-AI-SYNTHETIC",
                service_code="SYN-CEI-LAB-001",
                unit="panel",
                facility_scope_key="synthetic_tertiary",
                currency="CNY",
                amount_low_minor=8000,
                amount_high_minor=12000,
                economic_meaning="wholly_synthetic_reference_range",
                confidential=False,
            )
        )
        db.flush()
    pointer = db.scalar(
        select(GovernedActiveCareRelease).where(
            GovernedActiveCareRelease.release_type == release.release_type,
            GovernedActiveCareRelease.release_key == release.release_key,
            GovernedActiveCareRelease.scope_key == "controlled_synthetic_staging",
        )
    )
    if pointer is None:
        event = GovernedCareReleaseActivation(
            release_id=release.id,
            release_type=release.release_type,
            release_key=release.release_key,
            scope_key="controlled_synthetic_staging",
            action="activate",
            prior_release_id=None,
            reason_code="wholly_synthetic_fixture_bootstrap",
        )
        db.add(event)
        db.flush()
        db.add(
            GovernedActiveCareRelease(
                release_type=release.release_type,
                release_key=release.release_key,
                scope_key=event.scope_key,
                release_id=release.id,
                activation_event_id=event.id,
            )
        )
    elif pointer.release_id != release.id:
        raise RuntimeError("cei_fixture_price_pointer_conflict")


def bootstrap_synthetic_clinical_event_intelligence(
    db: Session,
    settings: Settings,
) -> SyntheticClinicalEventIntelligenceResult:
    if settings.environment not in {"local", "test"}:
        raise RuntimeError("cei_fixture_local_or_test_only")
    doctor_user, doctor, patient, membership = _accounts(db)
    hospital, clinic = _facility(db)
    event = db.scalar(
        select(ClinicalEvent).where(
            ClinicalEvent.patient_id == patient.id,
            ClinicalEvent.doctor_id == doctor.id,
            ClinicalEvent.metadata_json["fixture_key"].astext == FIXTURE_KEY,
        )
    )
    if event is None:
        event = ClinicalEvent(
            patient_id=patient.id,
            doctor_id=doctor.id,
            hospital_id=hospital.id,
            clinic_id=clinic.id,
            department_code=clinic.department_code,
            encounter_at=datetime(2026, 8, 2, 9, 0, tzinfo=UTC),
            title="CEI wholly synthetic two-line review",
            chief_complaint="Wholly synthetic mobility review fixture.",
            symptom_summary="Synthetic context only; no real patient information.",
            diagnosis_summary="Synthetic clinician-recorded rehabilitation context.",
            onset_date=date(2026, 7, 20),
            status="active",
            metadata_json={
                "fixture_key": FIXTURE_KEY,
                "data_class": "wholly_synthetic",
                "purpose": "clinical_event_intelligence_local_activation",
            },
        )
        db.add(event)
        db.flush()
    request = db.scalar(
        select(PayerRequest).where(
            PayerRequest.clinical_event_id == event.id,
            PayerRequest.doctor_summary == "Wholly synthetic CEI two-line immutable request.",
        )
    )
    if request is None:
        request = PayerRequest(
            clinical_event_id=event.id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            payer_organization_id=membership.payer_organization_id,
            status="submitted",
            currency="CNY",
            requested_total_minor=22000,
            doctor_summary="Wholly synthetic CEI two-line immutable request.",
            ai_review_status="not_evaluated",
        )
        request.lines.extend(
            [
                PayerRequestLine(
                    item_type="laboratory",
                    label="Synthetic rehabilitation safety panel",
                    code_system="DR-AI-SYNTHETIC",
                    service_code="SYN-CEI-LAB-001",
                    quantity=1,
                    unit="panel",
                    service_date=date(2026, 8, 2),
                    currency="CNY",
                    actual_cost_minor=10000,
                    requested_minor=10000,
                    patient_responsibility_minor=0,
                ),
                PayerRequestLine(
                    item_type="consultation",
                    label="Synthetic exploratory specialist review",
                    code_system="DR-AI-SYNTHETIC",
                    service_code="SYN-CEI-EXPLORATORY-001",
                    quantity=1,
                    unit="review",
                    service_date=date(2026, 8, 2),
                    currency="CNY",
                    actual_cost_minor=12000,
                    requested_minor=12000,
                    patient_responsibility_minor=0,
                ),
            ]
        )
        db.add(request)
        db.flush()
    elif len(request.lines) != 2:
        raise RuntimeError("cei_fixture_immutable_request_conflict")
    _price_release(db, payer_organization_id=membership.payer_organization_id)
    db.commit()
    request_id = request.id
    return SyntheticClinicalEventIntelligenceResult(
        payer_request_id=request_id,
        doctor_route=f"/doctor/payer-requests/{request_id}/intelligence",
        patient_route=f"/patient/payer-requests/{request_id}/intelligence",
        payer_route=f"/payer/requests/{request_id}/intelligence",
    )
