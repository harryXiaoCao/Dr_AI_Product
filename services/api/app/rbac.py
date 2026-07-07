from collections.abc import Collection

from app.errors import ApiError
from app.models import User, UserRole


def neutral_not_found() -> ApiError:
    return ApiError(404, "not_found", "The requested resource was not found.")


def require_enabled_role(user: User, allowed_roles: Collection[UserRole]) -> None:
    if user.role not in allowed_roles:
        raise ApiError(403, "forbidden", "This role is not enabled for this workflow.")
