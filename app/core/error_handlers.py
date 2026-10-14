"""Unified exception handlers conforming to the application error contract."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def _normalize_validation_loc(loc: tuple[Any, ...]) -> str:
    """Convert FastAPI/Pydantic error location tuple into a clean dot-notated string.

    Strips root prefixes such as 'body', 'query', 'header', and 'path' to expose
    a clear dot-notated field path (e.g. ('body', 'file') -> 'file').

    Args:
        loc (tuple[Any, ...]): Raw location tuple from validation error.

    Returns:
        str: Dot-notated field identifier.
    """
    cleaned_loc = list(loc)
    if cleaned_loc and cleaned_loc[0] in ("body", "query", "header", "path"):
        cleaned_loc.pop(0)

    if not cleaned_loc:
        return "unknown"

    return ".".join(str(part) for part in cleaned_loc)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application domain exceptions.

    Args:
        request (Request): Active HTTP request.
        exc (AppException): Raised application exception.

    Returns:
        JSONResponse: Standardized JSON error response.
    """
    logger.warning("Application exception [HTTP %s]: %s", exc.status_code, exc.message)
    content = {
        "success": False,
        "message": exc.message,
        "errors": exc.errors,
    }
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError | ValidationError
) -> JSONResponse:
    """Handle FastAPI and Pydantic validation errors with normalized dot paths.

    Args:
        request (Request): Active HTTP request.
        exc (RequestValidationError | ValidationError): Validation error instance.

    Returns:
        JSONResponse: Standardized JSON error response with HTTP 422.
    """
    errors: list[dict[str, str]] = []
    raw_errors = exc.errors() if hasattr(exc, "errors") else []

    for err in raw_errors:
        field_path = _normalize_validation_loc(err.get("loc", ()))
        message = err.get("msg", "Invalid value")
        errors.append({"field": field_path, "message": message})

    if not errors:
        errors.append({"field": "request", "message": "Validation error"})

    content = {
        "success": False,
        "message": "Request validation failed",
        "errors": errors,
    }
    return JSONResponse(status_code=422, content=content)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle Starlette and FastAPI HTTP exceptions.

    Args:
        request (Request): Active HTTP request.
        exc (StarletteHTTPException): Raised HTTP exception.

    Returns:
        JSONResponse: Standardized JSON error response matching the error contract.
    """
    message = exc.detail if isinstance(exc.detail, str) else "HTTP request error"
    content = {
        "success": False,
        "message": message,
        "errors": [{"field": "request", "message": message}],
    }
    return JSONResponse(status_code=exc.status_code, content=content)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions without leaking sensitive internal details.

    Args:
        request (Request): Active HTTP request.
        exc (Exception): Unhandled exception.

    Returns:
        JSONResponse: Generic HTTP 500 standardized JSON error response.
    """
    logger.exception("Unhandled server exception: %s", exc)
    content = {
        "success": False,
        "message": "Internal server error occurred",
        "errors": [
            {
                "field": "server",
                "message": "An unexpected error occurred while processing the request",
            }
        ],
    }
    return JSONResponse(status_code=500, content=content)


def register_error_handlers(app: FastAPI) -> None:
    """Register all unified exception handlers with the FastAPI application.

    Args:
        app (FastAPI): FastAPI application instance.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
