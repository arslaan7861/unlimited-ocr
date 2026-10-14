"""Middleware to track and correlate incoming HTTP requests via X-Request-ID."""

import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logger import request_id_ctx


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware that extracts or generates a unique correlation ID per request.

    The correlation ID is attached to:
    - contextvars (`request_id_ctx`) for logger injection
    - `request.state.request_id` for in-process route access
    - `X-Request-ID` response header
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process incoming request, propagate request ID, and attach response header.

        Args:
            request (Request): Active HTTP request.
            call_next (Callable): Next ASGI middleware/endpoint handler.

        Returns:
            Response: Outgoing HTTP response with X-Request-ID header attached.
        """
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Bind to contextvar for logger
        token = request_id_ctx.set(request_id)
        # Bind to request state
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)
