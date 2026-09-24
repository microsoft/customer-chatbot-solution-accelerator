from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.routers import auth as auth_router


def create_request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 503])
async def test_auth_me_preserves_authentication_http_errors(
    monkeypatch: pytest.MonkeyPatch, status_code: int
) -> None:
    error = HTTPException(status_code=status_code, detail="Authentication failed")
    monkeypatch.setattr(
        auth_router,
        "get_current_user",
        AsyncMock(side_effect=error),
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth_router.get_current_user_info(create_request())

    assert exc_info.value is error
