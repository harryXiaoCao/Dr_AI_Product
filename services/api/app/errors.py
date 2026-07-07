from collections.abc import Sequence

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Sequence[dict[str, str]] = (),
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = list(details)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: Sequence[dict[str, str]] = (),
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request.state.request_id,
                "details": list(details),
            }
        },
        headers={"X-Request-ID": request.state.request_id},
    )


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return error_response(request, exc.status_code, exc.code, exc.message, exc.details)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details: list[dict[str, str]] = []
    for error in exc.errors():
        location = error.get("loc", ())
        safe_location = [str(item) for item in location if item not in {"body"}]
        details.append(
            {
                "field": ".".join(safe_location) or "request",
                "code": "invalid_value",
                "message": "The supplied value is invalid.",
            }
        )
    return error_response(
        request,
        422,
        "validation_failed",
        "The request could not be validated.",
        details,
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    mapping: dict[int, tuple[str, str]] = {
        401: ("unauthenticated", "Authentication is required."),
        403: ("forbidden", "You do not have access to this resource."),
        404: ("not_found", "The requested resource was not found."),
        405: ("bad_request", "The request method is not supported."),
    }
    code, message = mapping.get(
        exc.status_code, ("bad_request", "The request could not be completed.")
    )
    return error_response(request, exc.status_code, code, message)


def safe_internal_error(request: Request, _: Exception) -> JSONResponse:
    return error_response(
        request,
        500,
        "internal_error",
        "The request could not be completed.",
    )
