from types import SimpleNamespace
from typing import Any

import pytest

from app.cosmos_service import CosmosDatabaseService


class StubContainer:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def query_items(self, **kwargs: Any):
        self.calls.append(kwargs)
        return iter([])


@pytest.mark.asyncio
async def test_get_chat_session_returns_none_without_user_id() -> None:
    container = StubContainer()
    service = SimpleNamespace(chat_container=container)

    result = await CosmosDatabaseService.get_chat_session(service, "session-a")  # type: ignore[arg-type]

    assert result is None
    assert container.calls == []


@pytest.mark.asyncio
async def test_get_chat_session_scopes_to_owner_partition() -> None:
    container = StubContainer()
    service = SimpleNamespace(chat_container=container)

    result = await CosmosDatabaseService.get_chat_session(service, "victim-session", "attacker-id")  # type: ignore[arg-type]

    assert result is None
    assert len(container.calls) == 1
    call = container.calls[0]
    assert call["partition_key"] == "attacker-id"
    assert "enable_cross_partition_query" not in call
    assert "c.user_id = @user_id" in call["query"]
    parameter_names = {param["name"] for param in call["parameters"]}
    assert parameter_names == {"@session_id", "@user_id"}
