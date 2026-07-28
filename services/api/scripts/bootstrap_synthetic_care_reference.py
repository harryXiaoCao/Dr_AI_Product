"""Install the wholly synthetic local care-reference integration bundle."""

from app.care_reference_integration import resolve_active_care_reference_bundle
from app.database import SessionLocal
from app.synthetic_care_reference import (
    install_all_synthetic_stage_reference_families,
    synthetic_active_selection,
)


def main() -> None:
    with SessionLocal() as session:
        families = install_all_synthetic_stage_reference_families(session)
        resolved = resolve_active_care_reference_bundle(
            session,
            selection=synthetic_active_selection(),
        )
        session.commit()
    installed = ", ".join(
        f"{family}:{name}={release.version}"
        for family, releases in families.items()
        for name, release in releases.items()
    )
    resolved_versions = (
        resolved.scenario.control.version,
        resolved.plan.control.version,
        resolved.pricing.control.version,
        resolved.utilization.control.version,
    )
    if len(set(resolved_versions)) != 1:
        raise RuntimeError("synthetic_active_bundle_version_mismatch")
    print(f"Activated and resolved wholly synthetic care-reference bundle: {installed}")


if __name__ == "__main__":
    main()
