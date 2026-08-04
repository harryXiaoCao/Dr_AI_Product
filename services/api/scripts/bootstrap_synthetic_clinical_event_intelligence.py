"""Create the dedicated local-only CEI fixture and print content-free routes."""

from app.config import get_settings
from app.database import SessionLocal
from app.synthetic_clinical_event_intelligence import (
    DOCTOR_EMAIL,
    LOCAL_ONLY_PASSWORD,
    PATIENT_EMAIL,
    PAYER_EMAIL,
    bootstrap_synthetic_clinical_event_intelligence,
)


def main() -> None:
    with SessionLocal() as db:
        result = bootstrap_synthetic_clinical_event_intelligence(db, get_settings())
    print("Wholly synthetic CEI fixture is ready.")
    print(f"doctor_email={DOCTOR_EMAIL}")
    print(f"patient_email={PATIENT_EMAIL}")
    print(f"payer_email={PAYER_EMAIL}")
    print(f"shared_local_only_password={LOCAL_ONLY_PASSWORD}")
    print(f"payer_request_id={result.payer_request_id}")
    print(f"doctor_route={result.doctor_route}")
    print(f"patient_route={result.patient_route}")
    print(f"payer_route={result.payer_route}")


if __name__ == "__main__":
    main()
