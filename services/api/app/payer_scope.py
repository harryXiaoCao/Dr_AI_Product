"""Fail-closed resolution of the payer reviewer's active organization."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.errors import ApiError
from app.models import PayerMembership, User, UserRole


def require_active_payer_membership(
    db: Session,
    user: User,
) -> PayerMembership:
    if user.role != UserRole.payer:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    memberships = db.scalars(
        select(PayerMembership)
        .options(selectinload(PayerMembership.organization))
        .where(
            PayerMembership.user_id == user.id,
            PayerMembership.status == "active",
        )
        .order_by(PayerMembership.created_at, PayerMembership.id)
    ).all()
    if not memberships:
        raise ApiError(404, "not_found", "The requested resource was not found.")
    if len(memberships) != 1:
        raise ApiError(
            409,
            "payer_organization_context_ambiguous",
            "The active payer organization could not be resolved.",
        )
    return memberships[0]
