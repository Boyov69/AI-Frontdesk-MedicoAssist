"""
Centralized error handlers for FastAPI.
Provides standardized JSON error responses across the entire API.
"""

import logging
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI):
    """Register all error handlers on the FastAPI app instance."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Standardized HTTP error responses."""
        logger.warning(
            "HTTP %d on %s %s: %s",
            exc.status_code, request.method, request.url.path, exc.detail
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Standardized validation error responses (422 → 400)."""
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")

        logger.warning(
            "Errore di validazione su %s %s: %s",
            request.method, request.url.path, "; ".join(errors)
        )
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Errore di validazione",
                "details": errors,
                "status_code": 400,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions."""
        logger.error(
            "Eccezione non gestita su %s %s: %s\n%s",
            request.method, request.url.path, str(exc), traceback.format_exc()
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Errore interno del server",
                "status_code": 500,
            },
        )
