"""
Domain errors and the JSON error envelope.

Business rules raise these (see ``app/crud/``). The handlers registered here
turn them into consistent HTTP responses, so every error the API returns has
exactly the same shape::

    {"error": {"code": "not_found", "message": "User 42 not found"}}

That is far friendlier for the frontend than five different formats.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for expected, user-facing errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class BadRequestError(AppError):
    """The request was understood but makes no sense (400)."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"


class NotFoundError(AppError):
    """The thing you asked for does not exist (404)."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    """The request clashes with the current state of the data (409).

    Examples: not enough stock, duplicate email, cancelling a cancelled order.
    """

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
) -> JSONResponse:
    """Build the standard error payload."""
    payload: dict[str, dict[str, Any]] = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the handlers that produce the envelope above."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            # Starlette renamed HTTP_422_UNPROCESSABLE_ENTITY to
            # ..._CONTENT; this is the current spelling.
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_error",
            "Request validation failed",
            details=jsonable_encoder(exc.errors()),
        )
