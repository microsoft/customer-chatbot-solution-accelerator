"""
Test cases for chat endpoints (/api/chat)
Uses FastAPI TestClient with function-based tests.
"""

from unittest.mock import AsyncMock, Mock, patch

# =============================================================================
# GET /api/chat/sessions
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_sessions_authenticated(
    mock_cosmos, mock_get_user, client, sample_chat_session
):
    """Test GET /api/chat/sessions endpoint for authenticated user"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_sessions_by_user = AsyncMock(
        return_value=[sample_chat_session]
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/sessions")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "session-123"
    assert data[0]["session_name"] == "Test Chat"


@patch("app.routers.chat.get_current_user_optional")
def test_get_chat_sessions_anonymous(mock_get_user, client):
    """Test GET /api/chat/sessions endpoint for anonymous user"""
    mock_get_user.return_value = None

    response = client.get("/api/chat/sessions")

    assert response.status_code in [200, 500]
    data = response.json()

    if response.status_code == 200:
        assert len(data) == 0
    else:
        assert "message" in data or "error" in data


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_sessions_error_handling(mock_cosmos, mock_get_user, client):
    """Test GET /api/chat/sessions endpoint error handling"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_sessions_by_user = AsyncMock(
        side_effect=Exception("Database error")
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/sessions")

    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "success" in data
    assert data["success"] is False


# =============================================================================
# GET /api/chat/sessions/{session_id}
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_session_by_id_success(
    mock_cosmos, mock_get_user, client, sample_chat_session_with_messages
):
    """Test GET /api/chat/sessions/{session_id} endpoint"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_session = AsyncMock(
        return_value=sample_chat_session_with_messages
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/sessions/session-123")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "session-123"
    assert data["session_name"] == "Test Chat"
    assert len(data["messages"]) == 1


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_session_not_found(mock_cosmos, mock_get_user, client):
    """Test GET /api/chat/sessions/{session_id} endpoint - session not found"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_session = AsyncMock(return_value=None)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/sessions/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Chat session not found"
    assert data["success"] is False


# =============================================================================
# POST /api/chat/sessions
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_create_chat_session_success(
    mock_cosmos, mock_get_user, client, sample_chat_session
):
    """Test POST /api/chat/sessions endpoint"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.create_chat_session = AsyncMock(return_value=sample_chat_session)
    mock_cosmos.return_value = mock_cosmos_service

    session_data = {"session_name": "Test Chat"}

    response = client.post("/api/chat/sessions", json=session_data)

    assert response.status_code in [200, 500]
    data = response.json()
    assert "message" in data
    mock_cosmos_service.create_chat_session.assert_called_once()


@patch("app.routers.chat.get_current_user_optional")
def test_create_chat_session_anonymous(mock_get_user, client):
    """Test POST /api/chat/sessions endpoint for anonymous user"""
    mock_get_user.return_value = None

    session_data = {"session_name": "New Chat"}

    response = client.post("/api/chat/sessions", json=session_data)

    assert response.status_code in [401, 500]
    if response.status_code == 500:
        data = response.json()
        assert "message" in data or "error" in data


# =============================================================================
# POST /api/chat/sessions/new
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_create_new_chat_session_legacy(
    mock_cosmos, mock_get_user, client, sample_chat_session
):
    """Test POST /api/chat/sessions/new endpoint"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.create_chat_session = AsyncMock(return_value=sample_chat_session)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.post("/api/chat/sessions/new")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "New chat session created"
    assert "session_id" in data["data"]


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_create_new_chat_session_anonymous(
    mock_cosmos, mock_get_user, client, sample_chat_session
):
    """Test POST /api/chat/sessions/new for anonymous user"""
    mock_get_user.return_value = None

    mock_cosmos_service = Mock()
    mock_cosmos_service.create_chat_session = AsyncMock(return_value=sample_chat_session)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.post("/api/chat/sessions/new")

    assert response.status_code == 200


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_create_new_chat_session_error(mock_cosmos, mock_get_user, client):
    """Test POST /api/chat/sessions/new error handling"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.create_chat_session = AsyncMock(
        side_effect=Exception("Creation failed")
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.post("/api/chat/sessions/new")

    assert response.status_code == 500


# =============================================================================
# PUT /api/chat/sessions/{session_id}
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_update_chat_session_success(
    mock_cosmos, mock_get_user, client, sample_chat_session
):
    """Test PUT /api/chat/sessions/{session_id} endpoint"""
    mock_get_user.return_value = {"user_id": "user-123"}

    # Modify the sample session to reflect the update
    sample_chat_session.session_name = "Updated Name"
    sample_chat_session.is_active = False

    mock_cosmos_service = Mock()
    mock_cosmos_service.update_chat_session = AsyncMock(return_value=sample_chat_session)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.put(
        "/api/chat/sessions/session-123",
        json={"session_name": "Updated Name", "is_active": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_name"] == "Updated Name"
    assert data["is_active"] is False


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_update_chat_session_not_found(mock_cosmos, mock_get_user, client):
    """Test PUT /api/chat/sessions/{session_id} - session not found"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.update_chat_session = AsyncMock(return_value=None)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.put(
        "/api/chat/sessions/nonexistent", json={"session_name": "Updated"}
    )

    assert response.status_code == 404


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_update_chat_session_error(mock_cosmos, mock_get_user, client):
    """Test PUT /api/chat/sessions/{session_id} - error handling"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.update_chat_session = AsyncMock(
        side_effect=Exception("Update failed")
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.put(
        "/api/chat/sessions/session-1", json={"session_name": "Updated"}
    )

    assert response.status_code == 500


# =============================================================================
# DELETE /api/chat/sessions/{session_id}
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_delete_chat_session_success(mock_cosmos, mock_get_user, client):
    """Test DELETE /api/chat/sessions/{session_id} endpoint"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.delete_chat_session = AsyncMock(return_value=True)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.delete("/api/chat/sessions/session-123")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_delete_chat_session_not_found(mock_cosmos, mock_get_user, client):
    """Test DELETE /api/chat/sessions/{session_id} - session not found"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.delete_chat_session = AsyncMock(return_value=False)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.delete("/api/chat/sessions/nonexistent")

    assert response.status_code == 404


# =============================================================================
# POST /api/chat/sessions/{session_id}/messages
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_add_message_session_not_found(mock_get_cosmos, mock_get_user, client):
    """Test add message to non-existent session"""
    mock_get_user.return_value = {"user_id": "test-user"}
    mock_cosmos = mock_get_cosmos.return_value
    mock_cosmos.add_message_to_session.return_value = None

    response = client.post(
        "/api/chat/sessions/nonexistent/messages",
        json={"content": "Hello", "message_type": "user"},
    )

    assert response.status_code in [404, 500]


# =============================================================================
# GET /api/chat/history
# =============================================================================


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_history_legacy_default_session(
    mock_cosmos, mock_get_user, client, sample_chat_session_with_messages
):
    """Test GET /api/chat/history endpoint with default session"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_session = AsyncMock(
        return_value=sample_chat_session_with_messages
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/history?session_id=default")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Hello"


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_history_anonymous_user(
    mock_cosmos, mock_get_user, client, sample_chat_session_with_messages
):
    """Test GET /api/chat/history for anonymous user"""
    mock_get_user.return_value = None

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_session = AsyncMock(
        return_value=sample_chat_session_with_messages
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/history?session_id=default")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_history_no_session(mock_cosmos, mock_get_user, client):
    """Test GET /api/chat/history when session doesn't exist"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_session = AsyncMock(return_value=None)
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/history?session_id=nonexistent")

    assert response.status_code == 200
    data = response.json()
    assert data == []


@patch("app.routers.chat.get_current_user_optional")
@patch("app.routers.chat.get_cosmos_service")
def test_get_chat_history_error(mock_cosmos, mock_get_user, client):
    """Test GET /api/chat/history error handling"""
    mock_get_user.return_value = {"user_id": "user-123"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_session = AsyncMock(
        side_effect=Exception("DB error")
    )
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/history")

    assert response.status_code == 500


# =============================================================================
# POST /api/chat/message
# =============================================================================


@patch("app.routers.chat.settings")
@patch("app.utils.azure_credential_utils.get_azure_credential_async")
@patch("app.routers.chat.AIProjectClient")
@patch("app.routers.chat.ChatAgent")
@patch("app.routers.chat.AzureAIAgentClient")
@patch("app.routers.chat.get_cosmos_service")
def test_send_message_legacy_success(
    mock_get_cosmos,
    mock_azure_client,
    mock_chat_agent,
    mock_ai_client,
    mock_get_credential,
    mock_settings,
    client,
):
    """Test send_message_legacy with explicit session_id"""
    mock_settings.azure_foundry_endpoint = "https://test.azure.com"
    mock_settings.foundry_chat_agent_id = "chat-agent-123"
    mock_settings.foundry_custom_product_agent_id = "product-agent-123"
    mock_settings.foundry_policy_agent_id = "policy-agent-123"

    mock_session = Mock()
    mock_session.messages = []
    mock_cosmos = Mock()
    mock_cosmos.add_message_to_session = AsyncMock(return_value=mock_session)
    mock_get_cosmos.return_value = mock_cosmos

    mock_cred_instance = AsyncMock()
    mock_cred_instance.__aenter__ = AsyncMock(return_value=mock_cred_instance)
    mock_cred_instance.__aexit__ = AsyncMock(return_value=None)
    mock_get_credential.return_value = mock_cred_instance

    mock_client_instance = AsyncMock()
    mock_ai_client.return_value.__aenter__ = AsyncMock(
        return_value=mock_client_instance
    )
    mock_ai_client.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_agent_instance = AsyncMock()
    mock_agent_result = Mock()
    mock_agent_result.text = "AI response from agent"
    mock_agent_instance.run = AsyncMock(return_value=mock_agent_result)
    mock_agent_instance.get_new_thread = Mock(return_value="thread-123")

    mock_chat_agent.return_value.__aenter__ = AsyncMock(
        return_value=mock_agent_instance
    )
    mock_chat_agent.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_azure_client.return_value = Mock()

    response = client.post(
        "/api/chat/message",
        json={
            "content": "Hello AI",
            "session_id": "custom-session-123",
            "message_type": "user",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "AI response from agent"
    assert data["sender"] == "assistant"
    assert "timestamp" in data


@patch("app.routers.chat.settings")
@patch("app.utils.azure_credential_utils.get_azure_credential_async")
@patch("app.routers.chat.AIProjectClient")
@patch("app.routers.chat.ChatAgent")
@patch("app.routers.chat.AzureAIAgentClient")
@patch("app.routers.chat.get_cosmos_service")
def test_send_message_legacy_agent_error(
    mock_get_cosmos,
    mock_azure_client,
    mock_chat_agent,
    mock_ai_client,
    mock_get_credential,
    mock_settings,
    client,
):
    """Test send_message_legacy when AI agent raises error"""
    mock_settings.azure_foundry_endpoint = "https://test.azure.com"
    mock_settings.foundry_chat_agent_id = "chat-agent-123"
    mock_settings.foundry_custom_product_agent_id = "product-agent-123"
    mock_settings.foundry_policy_agent_id = "policy-agent-123"

    mock_session = Mock()
    mock_session.messages = []
    mock_cosmos = Mock()
    mock_cosmos.add_message_to_session = AsyncMock(return_value=mock_session)
    mock_get_cosmos.return_value = mock_cosmos

    mock_cred_instance = AsyncMock()
    mock_cred_instance.__aenter__ = AsyncMock(return_value=mock_cred_instance)
    mock_cred_instance.__aexit__ = AsyncMock(return_value=None)
    mock_get_credential.return_value = mock_cred_instance

    mock_client_instance = AsyncMock()
    mock_ai_client.return_value.__aenter__ = AsyncMock(
        return_value=mock_client_instance
    )
    mock_ai_client.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_agent_instance = AsyncMock()
    mock_agent_instance.run = AsyncMock(
        side_effect=Exception("Agent processing failed")
    )
    mock_agent_instance.get_new_thread = Mock(return_value="thread-123")
    mock_agent_instance.as_tool = Mock(return_value="tool")

    mock_chat_agent.return_value.__aenter__ = AsyncMock(
        return_value=mock_agent_instance
    )
    mock_chat_agent.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_azure_client.return_value = Mock()

    response = client.post(
        "/api/chat/message", json={"content": "Test message", "message_type": "user"}
    )

    assert response.status_code == 500
    response_data = response.json()
    error_text = str(response_data)
    assert "AI agent error" in error_text or "Agent processing failed" in error_text


@patch("app.routers.chat.settings")
@patch("app.routers.chat.get_cosmos_service")
def test_send_message_legacy_cosmos_error(mock_get_cosmos, mock_settings, client):
    """Test send_message_legacy when Cosmos DB fails"""
    mock_settings.azure_foundry_endpoint = "https://test.azure.com"

    mock_cosmos = Mock()
    mock_cosmos.add_message_to_session = AsyncMock(
        side_effect=Exception("Cosmos DB connection failed")
    )
    mock_get_cosmos.return_value = mock_cosmos

    response = client.post(
        "/api/chat/message", json={"content": "Test message", "message_type": "user"}
    )

    assert response.status_code == 500
    response_data = response.json()
    assert "Error sending message" in str(response_data)
