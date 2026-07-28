"""Create the idempotent local-only Slice E interactive demonstration."""

from app.config import get_settings
from app.database import SessionLocal
from app.synthetic_expected_care_demo import (
    bootstrap_synthetic_expected_care_demo,
)


def main() -> None:
    with SessionLocal() as db:
        result = bootstrap_synthetic_expected_care_demo(db, get_settings())
    print("Wholly synthetic Slice E demonstration is ready:")
    print(f"doctor={result.doctor_route}")
    print(f"patient={result.patient_route}")
    print(f"payer={result.payer_route}")
    print(
        "unresponded_candidate_result_id="
        f"{result.unresponded_candidate_result_id}"
    )
    print(f"published_baseline_id={result.published_baseline_id}")


if __name__ == "__main__":
    main()
