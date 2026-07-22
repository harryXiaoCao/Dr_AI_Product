from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import engine
from app.knowledge_ingestion import activate_index_release
from app.models import KbIndexRelease


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Activate a patient retrieval candidate only after a passing Slice 9A artifact."
    )
    parser.add_argument("--release-id", type=uuid.UUID, required=True)
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--activated-by", required=True)
    args = parser.parse_args()

    evaluation = json.loads(args.evaluation.read_text())
    evaluated_release_id = evaluation.get("release", {}).get("release_id")
    if evaluation.get("suite_id") != "dr-ai-slice9a-retrieval-v2":
        raise SystemExit("The supplied artifact is not the frozen Slice 9A evaluation.")
    if evaluation.get("review", {}).get("status") != "approved":
        raise SystemExit("The Slice 9A suite in the artifact lacks clinician approval.")
    if not evaluation.get("passed") or evaluation.get("failures"):
        raise SystemExit("The Slice 9A artifact did not pass every gate; activation refused.")
    if evaluated_release_id != str(args.release_id):
        raise SystemExit("The evaluation artifact belongs to a different release.")

    with Session(engine) as db:
        release = db.get(KbIndexRelease, args.release_id)
        if release is None or release.status != "built":
            raise SystemExit("Candidate release does not exist or is not in built status.")
        if release.stable_id != evaluation.get("release", {}).get("stable_id"):
            raise SystemExit("Candidate release lineage does not match the evaluation artifact.")
        activate_index_release(
            db,
            release,
            audience="patient",
            activated_by=args.activated_by,
        )
        db.commit()
        print(
            json.dumps(
                {
                    "release_id": str(release.id),
                    "stable_id": release.stable_id,
                    "status": release.status,
                    "activated_by": args.activated_by,
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
