from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import engine
from app.patient_knowledge_release import (
    active_patient_release_version_ids,
    build_patient_candidate_release,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-embed the active patient corpus into a non-active immutable candidate."
    )
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--approver-id", required=True)
    parser.add_argument("--batch-size", type=int, default=30)
    args = parser.parse_args()

    with Session(engine) as db:
        version_ids = active_patient_release_version_ids(db)
        if not version_ids:
            raise SystemExit("No active patient release exists; candidate build refused.")
        release = build_patient_candidate_release(
            db,
            version_ids=version_ids,
            artifact_root=args.artifact_root,
            approver_id=args.approver_id,
            embedding_batch_size=args.batch_size,
        )
        db.commit()
        print(
            json.dumps(
                {
                    "release_id": str(release.id),
                    "stable_id": release.stable_id,
                    "status": release.status,
                    "passage_count": release.passage_count,
                    "embedding_model": release.embedding_model_version,
                    "reranker_model": release.reranker_version,
                    "active": False,
                },
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
