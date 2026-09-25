"""ASGI middleware that validates the Entra bearer token once per request."""

import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from .auth import STATE_ATTR, resolve_bearer_user
except ImportError:
    from app.auth import STATE_ATTR, resolve_bearer_user

logger = logging.getLogger(__name__)


class EntraAuthMiddleware(BaseHTTPMiddleware):
    """Validate the Authorization header and stash the resolved user on request.state."""

    async def dispatch(self, request: Request, call_next):
        try:
            user = await resolve_bearer_user(request)
        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=dict(exc.headers or {}),
            )
        setattr(request.state, STATE_ATTR, user)
        return await call_next(request)
