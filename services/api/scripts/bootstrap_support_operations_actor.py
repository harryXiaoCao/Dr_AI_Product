"""Create the non-login synthetic actor used for support lifecycle rehearsals."""

import secrets

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import User, UserRole
from app.security import hash_password

ACTOR_EMAIL = "phase5.support.operations@synthetic.invalid"


def main() -> None:
    settings = get_settings()
    if settings.environment not in {"local", "test", "staging"}:
        raise SystemExit(
            "The synthetic support-operations actor is restricted to local, "
            "test, and controlled staging environments."
        )

    with SessionLocal() as db:
        actor = db.scalar(
            select(User).where(
                User.email == ACTOR_EMAIL,
                User.role == UserRole.admin,
            )
        )
        created = actor is None
        if actor is None:
            actor = User(
                email=ACTOR_EMAIL,
                password_hash=hash_password(secrets.token_urlsafe(48)),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(actor)
            db.flush()
        elif not actor.is_active:
            raise SystemExit(
                "The existing synthetic support-operations actor is disabled; "
                "do not reactivate it implicitly."
            )
        db.commit()
        actor_id = actor.id

    state = "created" if created else "reused"
    print(f"{state}: actor_user_id={actor_id}")


if __name__ == "__main__":
    main()
