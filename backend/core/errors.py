"""Consistent API error envelope.

Every error response has the shape:

    {"error": {"code": "...", "message": "...", "details": [...] | null}}

- ApiError: raise from endpoints for structured errors (e.g. schema validation)
- HTTPException: converted automatically (detail becomes the message)
- RequestValidationError: 422 with per-field details and a readable message
"""

from typing import Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

STATUS_CODE_NAMES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    500: "internal_error",
}


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        code: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.code = code or STATUS_CODE_NAMES.get(status_code, "error")
        self.details = details


def envelope(code: str, message: str, details: Optional[Any] = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def format_pydantic_errors(errors: List[dict]) -> List[dict]:
    """Turn pydantic/fastapi error dicts into [{field, message}, ...]."""
    formatted = []
    for err in errors:
        loc = [str(part) for part in err.get("loc", ()) if part != "body"]
        formatted.append({
            "field": ".".join(loc) or "(request)",
            "message": err.get("msg", "Invalid value"),
        })
    return formatted


def validation_message(details: List[dict]) -> str:
    parts = [f"{d['field']}: {d['message']}" for d in details]
    return "Validation failed — " + "; ".join(parts) if parts else "Validation failed"


def schema_validation_error(exc) -> ApiError:
    """Build a 400 ApiError from a pydantic ValidationError against an
    entry-type template."""
    details = format_pydantic_errors(exc.errors())
    return ApiError(400, validation_message(details), code="validation_error", details=details)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code,
            content=envelope(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = STATUS_CODE_NAMES.get(exc.status_code, "error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        details = None if isinstance(exc.detail, str) else exc.detail
        return JSONResponse(
            status_code=exc.status_code,
            content=envelope(code, message, details),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError):
        details = format_pydantic_errors(exc.errors())
        return JSONResponse(
            status_code=422,
            content=envelope("validation_error", validation_message(details), details),
        )
