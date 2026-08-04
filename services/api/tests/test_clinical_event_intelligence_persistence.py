import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.clinical_event_intelligence_contracts import canonical_checksum
from app.database import engine
from app.models import (
    Clinic,
    ClinicalEvent,
    ClinicalEventIntelligenceArtifact,
    ClinicalEventIntelligenceItemAssessment,
    ClinicalEventIntelligencePathway,
    ClinicalEventIntelligencePathwayItem,
    ClinicalEventIntelligenceProviderAttempt,
    ClinicalEventIntelligenceRetrievalSource,
    ClinicalEventIntelligenceRun,
    ClinicalEventIntelligenceSnapshot,
    ClinicalService,
    DoctorProfile,
    GovernedCareRelease,
    Hospital,
    PatientProfile,
    PayerDoctorResponse,
    PayerOrganization,
    PayerRequest,
    PayerRequestLine,
    RoleAssignment,
    User,
    UserRole,
)
from app.seed import seed_database


def _fixture(db: Session, settings):
    seed_database(db, settings)
    doctor_user = db.scalar(select(User).where(User.email == "doctor.demo@example.com"))
    patient_user = db.scalar(select(User).where(User.email == "patient.demo@example.com"))
    assert doctor_user is not None and patient_user is not None
    doctor = db.scalar(select(DoctorProfile).where(DoctorProfile.user_id == doctor_user.id))
    patient = db.scalar(select(PatientProfile).where(PatientProfile.user_id == patient_user.id))
    assert doctor is not None and patient is not None
    event = ClinicalEvent(
        patient_id=patient.id,
        doctor_id=doctor.id,
        title="Synthetic provider unavailable event",
        chief_complaint="Wholly synthetic persistence fixture",
    )
    payer = PayerOrganization(name=f"Synthetic payer {uuid.uuid4()}")
    db.add_all([event, payer])
    db.flush()
    request = PayerRequest(
        clinical_event_id=event.id,
        patient_id=patient.id,
        doctor_id=doctor.id,
        payer_organization_id=payer.id,
        requested_total_minor=30_000,
        doctor_summary="Wholly synthetic immutable request.",
    )
    db.add(request)
    db.flush()
    lines = [
        PayerRequestLine(
            payer_request_id=request.id,
            item_type="synthetic_service",
            label=f"Synthetic requested item {index}",
            code_system="DR-AI-SYNTHETIC",
            service_code=f"SYN-{index}",
            quantity=1,
            unit="item",
            service_date=date(2026, 8, 1),
            currency="CNY",
            actual_cost_minor=10_000 * index,
            requested_minor=10_000 * index,
            patient_responsibility_minor=0,
        )
        for index in (1, 2)
    ]
    release = GovernedCareRelease(
        release_type="clinical_event_intelligence_primary",
        release_key="synthetic-cei-primary",
        version="v1-test",
        schema_version="clinical-event-intelligence-output.v1",
        lifecycle_status="reviewed",
        jurisdiction="synthetic_only",
        facility_scope_json={},
        currency="CNY",
        effective_from=date(2026, 8, 1),
        source_authority="Wholly synthetic persistence test",
        source_locator="urn:dr-ai:synthetic:cei-primary",
        retrieved_at=datetime(2026, 8, 1, tzinfo=UTC),
        source_checksum_sha256="a" * 64,
        payload_checksum_sha256="b" * 64,
        required_review_types_json=["synthetic_stage"],
        rights_status="product_owner_waived_for_current_stage",
        storage_allowed=True,
        derivation_allowed=True,
        provider_transmission_allowed=True,
    )
    db.add_all([*lines, release])
    db.flush()
    snapshot_checksum = canonical_checksum({"request_id": str(request.id), "version": 1})
    snapshot = ClinicalEventIntelligenceSnapshot(
        payer_request_id=request.id,
        snapshot_version=1,
        payer_request_version=request.version,
        patient_id=patient.id,
        clinical_event_id=event.id,
        doctor_id=doctor.id,
        payer_organization_id=payer.id,
        hospital_id=None,
        clinic_id=None,
        department_code=None,
        jurisdiction_code=None,
        province=None,
        city=None,
        facility_level=None,
        encounter_at=None,
        service_date_from=date(2026, 8, 1),
        service_date_to=date(2026, 8, 1),
        snapshot_contract_version="clinical-event-intelligence-snapshot.v1",
        snapshot_checksum_sha256=snapshot_checksum,
        snapshot_json={"data_class": "wholly_synthetic"},
        source_lineage_json=[],
        quality_flags_json=[{"code": "structured_location_missing"}],
    )
    db.add(snapshot)
    db.flush()
    return doctor_user, request, lines, release, snapshot


def _run(db, *, actor, request, release, snapshot, version):
    run = ClinicalEventIntelligenceRun(
        snapshot_id=snapshot.id,
        actor_user_id=actor.id,
        payer_request_id=request.id,
        run_version=version,
        idempotency_key=f"provider-unavailable-{version}",
        request_checksum_sha256=canonical_checksum({"run": version}),
        purpose_code="clinical_event_intelligence_primary",
        purpose_contract_version="clinical-event-intelligence-primary.v1",
        schema_version="clinical-event-intelligence-output.v1",
        prompt_version="clinical-event-intelligence-primary-prompt.v1",
        model_configuration_version="clinical-event-intelligence-model.v1",
        validator_version="clinical-event-intelligence-validator.v1",
        score_version="clinical-event-intelligence-score.v1",
        primary_release_id=release.id,
        lifecycle_state="provider_unavailable",
    )
    db.add(run)
    db.flush()
    return run


def _fallback(lines):
    return [
        {
            "requested_line_id": str(line.id),
            "state": "assessment_unavailable",
            "human_review_required": True,
            "no_automatic_action": True,
        }
        for line in lines
    ]


def _insert_artifact(db, *, request, snapshot, run, version, fallback):
    db.execute(
        insert(ClinicalEventIntelligenceArtifact).values(
            id=uuid.uuid4(),
            run_id=run.id,
            payer_request_id=request.id,
            artifact_version=version,
            lifecycle_state="provider_unavailable",
            requested_set_checksum_sha256="c" * 64,
            snapshot_checksum_sha256=snapshot.snapshot_checksum_sha256,
            result_checksum_sha256="d" * 64,
            configuration_checksum_sha256="e" * 64,
            reconciliation_checksum_sha256="f" * 64,
            disagreement_state="unavailable",
            artifact_json={"requested_item_assessments": fallback},
            validation_json={"provider_unavailable": True},
        )
    )
    db.flush()


def _guarded_children(db, *, run, release, lines):
    source = ClinicalEventIntelligenceRetrievalSource(
        run_id=run.id,
        ordinal=1,
        source_type="regional_reference",
        governed_release_id=release.id,
        provenance_tier=2,
        scope_checksum_sha256="1" * 64,
        lineage_checksum_sha256="2" * 64,
        source_lineage_json={"data_class": "wholly_synthetic"},
    )
    pathway = ClinicalEventIntelligencePathway(
        run_id=run.id,
        pathway_key="typical-first-line",
        pathway_type="typical_first_line",
        usefulness="Synthetic pathway used only to verify persistence guards.",
        confidence=50,
        supporting_facts_json=[],
        contradicting_facts_json=[],
        missing_information_json=[],
        assumptions_json=[],
    )
    attempt = ClinicalEventIntelligenceProviderAttempt(
        run_id=run.id,
        pass_type="primary",
        attempt_number=1,
        provider="synthetic_provider",
        model="synthetic_model",
        outcome="validated",
        latency_ms=0,
        input_tokens=0,
        output_tokens=0,
        cost_microunits=0,
        output_checksum_sha256="3" * 64,
    )
    db.add_all([source, pathway, attempt])
    db.flush()
    pathway_item = ClinicalEventIntelligencePathwayItem(
        pathway_id=pathway.id,
        item_key="predicted-only-item",
        label="Synthetic predicted item",
        unit="item",
        quantity_low=0,
        quantity_high=1,
        currency="CNY",
        cost_low_minor=0,
        cost_high_minor=1_000,
        predicted_only=True,
    )
    db.add(pathway_item)
    for line in lines:
        db.add(
            ClinicalEventIntelligenceItemAssessment(
                run_id=run.id,
                payer_request_line_id=line.id,
                retrieval_source_id=source.id,
                requested_label=line.label,
                requested_code=line.service_code,
                requested_quantity=line.quantity,
                requested_unit=line.unit,
                requested_amount_minor=line.requested_minor,
                currency=line.currency,
                estimated_quantity_low=0,
                estimated_quantity_high=2,
                estimated_cost_low_minor=0,
                estimated_cost_high_minor=20_000,
                clinical_fit=50,
                evidence_support=50,
                timing_sequence=50,
                quantity_intensity=50,
                documentation_completeness=50,
                cost_alignment=50,
                cost_alignment_weight_bp=1_000,
                ai_support_score=50,
                support_band="materially_uncertain",
                score_version="clinical-event-intelligence-score.v1",
                provenance_tier=2,
                exploratory=False,
                wide_uncertainty=False,
                confidence=50,
                usefulness="Synthetic normalized assessment for persistence verification.",
                mapped_pathways_json=[{"pathway_key": pathway.pathway_key}],
                supporting_facts_json=[],
                contradicting_facts_json=[],
                missing_information_json=[],
                alternatives_json=[],
                source_lineage_json=[{"source_id": str(source.id)}],
                brief_comments_json=[],
                validation_results_json={"validated": True},
                disagreement_state="agreement",
            )
        )
    db.flush()
    return source, pathway, pathway_item, attempt


def _insert_validated_artifact(db, *, request, snapshot, run, version):
    db.execute(
        insert(ClinicalEventIntelligenceArtifact).values(
            id=uuid.uuid4(),
            run_id=run.id,
            payer_request_id=request.id,
            artifact_version=version,
            lifecycle_state="validated",
            requested_set_checksum_sha256="4" * 64,
            snapshot_checksum_sha256=snapshot.snapshot_checksum_sha256,
            result_checksum_sha256="5" * 64,
            configuration_checksum_sha256="6" * 64,
            reconciliation_checksum_sha256="7" * 64,
            disagreement_state="agreement",
            artifact_json={"requested_item_assessments": []},
            validation_json={"validated": True},
        )
    )
    db.flush()


def test_run_open_trigger_handles_direct_run_and_pathway_item_records(settings) -> None:
    with Session(engine) as db:
        actor, request, _, release, snapshot = _fixture(db, settings)
        run = _run(
            db,
            actor=actor,
            request=request,
            release=release,
            snapshot=snapshot,
            version=1,
        )
        attempt_id = uuid.uuid4()
        db.execute(
            insert(ClinicalEventIntelligenceProviderAttempt).values(
                id=attempt_id,
                run_id=run.id,
                pass_type="primary",
                attempt_number=1,
                provider="synthetic_provider",
                model="synthetic_model",
                outcome="validated",
                latency_ms=1,
            )
        )
        pathway_id = uuid.uuid4()
        db.execute(
            insert(ClinicalEventIntelligencePathway).values(
                id=pathway_id,
                run_id=run.id,
                pathway_key="trigger-field-resolution",
                pathway_type="typical_first_line",
                usefulness="Synthetic trigger field-resolution regression.",
                confidence=50,
                supporting_facts_json=[],
                contradicting_facts_json=[],
                missing_information_json=[],
                assumptions_json=[],
            )
        )
        pathway_item_id = uuid.uuid4()
        db.execute(
            insert(ClinicalEventIntelligencePathwayItem).values(
                id=pathway_item_id,
                pathway_id=pathway_id,
                item_key="trigger-item",
                label="Synthetic trigger item",
                unit="item",
                quantity_low=0,
                quantity_high=1,
                currency="CNY",
                cost_low_minor=0,
                cost_high_minor=100,
                predicted_only=True,
            )
        )
        db.flush()
        assert db.get(ClinicalEventIntelligenceProviderAttempt, attempt_id) is not None
        assert db.get(ClinicalEventIntelligencePathwayItem, pathway_item_id) is not None


def test_guarded_children_insert_before_close_and_reject_after_close(settings) -> None:
    with Session(engine) as db:
        actor, request, lines, release, snapshot = _fixture(db, settings)
        run = _run(db, actor=actor, request=request, release=release, snapshot=snapshot, version=1)
        source, pathway, _, _ = _guarded_children(db, run=run, release=release, lines=lines)
        other_run = _run(
            db, actor=actor, request=request, release=release, snapshot=snapshot, version=2
        )
        with pytest.raises(DBAPIError, match="retrieval source belongs to another run"):
            with db.begin_nested():
                db.execute(
                    insert(ClinicalEventIntelligenceItemAssessment).values(
                        run_id=other_run.id,
                        retrieval_source_id=source.id,
                    )
                )
        _insert_validated_artifact(db, request=request, snapshot=snapshot, run=run, version=1)

        blocked_inserts = (
            insert(ClinicalEventIntelligenceRetrievalSource).values(run_id=run.id),
            insert(ClinicalEventIntelligencePathway).values(run_id=run.id),
            insert(ClinicalEventIntelligencePathwayItem).values(pathway_id=pathway.id),
            insert(ClinicalEventIntelligenceProviderAttempt).values(run_id=run.id),
            insert(ClinicalEventIntelligenceItemAssessment).values(run_id=run.id),
        )
        for statement in blocked_inserts:
            with pytest.raises(DBAPIError, match="clinical intelligence run is closed"):
                with db.begin_nested():
                    db.execute(statement)
                    db.flush()


def test_snapshot_facility_accepts_event_service_or_active_doctor_assignment(settings) -> None:
    with Session(engine) as db:
        _, request, _, _, original_snapshot = _fixture(db, settings)
        doctor = db.get(DoctorProfile, request.doctor_id)
        assert doctor is not None
        service_hospital = Hospital(name=f"Synthetic service hospital {uuid.uuid4()}")
        role_hospital = Hospital(name=f"Synthetic role hospital {uuid.uuid4()}")
        unrelated_hospital = Hospital(name=f"Synthetic unrelated hospital {uuid.uuid4()}")
        db.add_all([service_hospital, role_hospital, unrelated_hospital])
        db.flush()
        service_clinic = Clinic(hospital_id=service_hospital.id, name="Synthetic service clinic")
        role_clinic = Clinic(hospital_id=role_hospital.id, name="Synthetic role clinic")
        unrelated_clinic = Clinic(
            hospital_id=unrelated_hospital.id, name="Synthetic unrelated clinic"
        )
        db.add_all([service_clinic, role_clinic, unrelated_clinic])
        db.flush()
        db.add_all(
            [
                ClinicalService(
                    patient_id=request.patient_id,
                    clinical_event_id=request.clinical_event_id,
                    category="synthetic_service",
                    name="Synthetic event-linked service",
                    ordered_by_doctor_id=request.doctor_id,
                    clinic_id=service_clinic.id,
                    status="ordered",
                ),
                RoleAssignment(
                    user_id=doctor.user_id,
                    role=UserRole.doctor,
                    hospital_id=role_hospital.id,
                    clinic_id=role_clinic.id,
                    status="active",
                ),
            ]
        )
        db.flush()

        def add_snapshot(version, hospital, clinic):
            row = ClinicalEventIntelligenceSnapshot(
                predecessor_snapshot_id=original_snapshot.id,
                payer_request_id=request.id,
                snapshot_version=version,
                payer_request_version=request.version,
                patient_id=request.patient_id,
                clinical_event_id=request.clinical_event_id,
                doctor_id=request.doctor_id,
                payer_organization_id=request.payer_organization_id,
                hospital_id=hospital.id,
                clinic_id=clinic.id,
                department_code=None,
                jurisdiction_code=None,
                province=None,
                city=None,
                facility_level=None,
                encounter_at=None,
                service_date_from=date(2026, 8, 1),
                service_date_to=date(2026, 8, 1),
                snapshot_contract_version="clinical-event-intelligence-snapshot.v1",
                snapshot_checksum_sha256=canonical_checksum({"snapshot": version}),
                snapshot_json={"data_class": "wholly_synthetic"},
                source_lineage_json=[],
                quality_flags_json=[],
            )
            db.add(row)
            db.flush()

        add_snapshot(2, service_hospital, service_clinic)
        add_snapshot(3, role_hospital, role_clinic)
        with pytest.raises(DBAPIError, match="facility scope mismatch"):
            with db.begin_nested():
                add_snapshot(4, unrelated_hospital, unrelated_clinic)


def test_payer_doctor_response_is_append_only_for_lineage(settings) -> None:
    with Session(engine) as db:
        _, request, _, _, _ = _fixture(db, settings)
        response = PayerDoctorResponse(
            payer_request_id=request.id,
            doctor_id=request.doctor_id,
            response_type="acknowledge",
            summary="Wholly synthetic immutable clinician response.",
            request_checksum="8" * 64,
            idempotency_key="synthetic-lineage-response",
            version=1,
        )
        db.add(response)
        db.flush()
        for statement in (
            update(PayerDoctorResponse)
            .where(PayerDoctorResponse.id == response.id)
            .values(summary="Mutated"),
            delete(PayerDoctorResponse).where(PayerDoctorResponse.id == response.id),
        ):
            with pytest.raises(DBAPIError, match="append-only"):
                with db.begin_nested():
                    db.execute(statement)


def test_provider_unavailable_artifact_requires_exact_safe_fallback_lines(settings) -> None:
    with Session(engine) as db:
        actor, request, lines, release, snapshot = _fixture(db, settings)
        valid_run = _run(
            db, actor=actor, request=request, release=release, snapshot=snapshot, version=1
        )
        _insert_artifact(
            db,
            request=request,
            snapshot=snapshot,
            run=valid_run,
            version=1,
            fallback=_fallback(lines),
        )

        invalid_payloads = [
            _fallback(lines)[:-1],
            [_fallback(lines)[0], _fallback(lines)[0]],
            [*_fallback(lines), {**_fallback(lines)[0], "requested_line_id": str(uuid.uuid4())}],
        ]
        for version, payload in enumerate(invalid_payloads, 2):
            run = _run(
                db,
                actor=actor,
                request=request,
                release=release,
                snapshot=snapshot,
                version=version,
            )
            with pytest.raises(DBAPIError, match="represent every requested line exactly once"):
                with db.begin_nested():
                    _insert_artifact(
                        db,
                        request=request,
                        snapshot=snapshot,
                        run=run,
                        version=version,
                        fallback=payload,
                    )
