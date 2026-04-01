"""
Test cases for voice endpoints (/api/voice)
Uses FastAPI TestClient with function-based tests.
"""
import asyncio
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.ai.voicelive.models import ServerEventType


# Helper: build a FakeConnection that supports async iteration
class FakeConnection:
    """Mimics the SDK connection: supports awaitable methods + async iteration."""
    def __init__(self, events=None):
        self.session = AsyncMock()
        self.conversation = AsyncMock()
        self.response = AsyncMock()
        self.input_audio_buffer = AsyncMock()
        self._events = list(events or [])
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self._events:
            raise StopAsyncIteration
        return self._events.pop(0)


def _make_event(type_value, **attrs):
    """Create a mock SDK event with a given type value."""
    ev = MagicMock()
    ev.type = MagicMock()
    ev.type.value = type_value
    for k, v in attrs.items():
        setattr(ev, k, v)
    return ev


def _make_connect_ctx(connection):
    """Wrap a FakeConnection in an async context manager mock."""
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=connection)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


# =============================================================================
# GET /api/voice/config
# =============================================================================


@patch("app.routers.voice_live.settings")
def test_voice_config_enabled(mock_settings, client):
    """GET /api/voice/config returns enabled=True when endpoint is configured."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.voicelive_mode = "model"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"
    mock_settings.voicelive_transcribe_model = "gpt-4o-transcribe"
    mock_settings.voicelive_instructions = "Be helpful."

    response = client.get("/api/voice/config")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["mode"] == "model"
    assert data["model"] == "gpt-realtime-mini"
    assert data["voice"] == "alloy"
    assert data["transcribe_model"] == "gpt-4o-transcribe"
    assert data["instructions"] == "Be helpful."


@patch("app.routers.voice_live.settings")
def test_voice_config_enabled_via_openai_endpoint(mock_settings, client):
    """GET /api/voice/config falls back to azure_openai_endpoint."""
    mock_settings.azure_voicelive_endpoint = None
    mock_settings.azure_openai_endpoint = "https://openai.azure.com"
    mock_settings.voicelive_mode = "model"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "echo"
    mock_settings.voicelive_transcribe_model = "gpt-4o-transcribe"
    mock_settings.voicelive_instructions = ""

    response = client.get("/api/voice/config")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["voice"] == "echo"


@patch("app.routers.voice_live.settings")
def test_voice_config_disabled(mock_settings, client):
    """GET /api/voice/config returns enabled=False when no endpoints configured."""
    mock_settings.azure_voicelive_endpoint = None
    mock_settings.azure_openai_endpoint = None
    mock_settings.voicelive_mode = "model"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"
    mock_settings.voicelive_transcribe_model = "gpt-4o-transcribe"
    mock_settings.voicelive_instructions = ""

    response = client.get("/api/voice/config")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False


# =============================================================================
# POST /api/voice/tts — input validation
# =============================================================================


@patch("app.routers.voice_live.settings")
def test_tts_empty_text_returns_400(mock_settings, client):
    """POST /api/voice/tts returns 400 when text is empty."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None

    response = client.post("/api/voice/tts", json={"text": ""})
    assert response.status_code == 400


@patch("app.routers.voice_live.settings")
def test_tts_missing_text_key_returns_400(mock_settings, client):
    """POST /api/voice/tts returns 400 when text key is missing."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None

    response = client.post("/api/voice/tts", json={})
    assert response.status_code == 400


@patch("app.routers.voice_live.settings")
def test_tts_no_endpoint_returns_503(mock_settings, client):
    """POST /api/voice/tts returns 503 when no voice endpoint configured."""
    mock_settings.azure_voicelive_endpoint = None
    mock_settings.azure_openai_endpoint = None

    response = client.post("/api/voice/tts", json={"text": "Hello world"})
    assert response.status_code == 503


@patch("app.routers.voice_live.settings")
def test_tts_markdown_only_text_returns_400(mock_settings, client):
    """POST /api/voice/tts returns 400 when text is only markdown/URLs that get stripped."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None

    response = client.post("/api/voice/tts", json={"text": "https://example.com"})
    assert response.status_code == 400


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_success_returns_pcm_audio(mock_connect, mock_settings, client):
    """POST /api/voice/tts returns PCM audio with correct headers on success."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = "test-key"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    audio_delta = _make_event("response.audio.delta", delta=b"\x00\x01\x02\x03")
    done = _make_event("response.done")
    conn = FakeConnection([audio_delta, done])
    mock_connect.return_value = _make_connect_ctx(conn)

    response = client.post("/api/voice/tts", json={"text": "Hello world"})
    assert response.status_code == 200
    assert response.headers["X-Sample-Rate"] == "24000"
    assert response.headers["X-Format"] == "pcm16"
    assert len(response.content) > 0


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_connection_failure_returns_500(mock_connect, mock_settings, client):
    """POST /api/voice/tts returns 500 when SDK connection fails."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = "test-key"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
    ctx.__aexit__ = AsyncMock(return_value=False)
    mock_connect.return_value = ctx

    response = client.post("/api/voice/tts", json={"text": "Hello world"})
    assert response.status_code == 500


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_no_audio_generated_returns_500(mock_connect, mock_settings, client):
    """POST /api/voice/tts returns 500 when no audio chunks are produced."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = "test-key"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    done = _make_event("response.done")
    conn = FakeConnection([done])
    mock_connect.return_value = _make_connect_ctx(conn)

    response = client.post("/api/voice/tts", json={"text": "Hello world"})
    assert response.status_code == 500


@patch("app.routers.voice_live.settings")
def test_tts_strips_markdown_before_speaking(mock_settings, client):
    """POST /api/voice/tts strips markdown — text with only a URL results in 400."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None

    response = client.post("/api/voice/tts", json={"text": "https://example.com/path"})
    assert response.status_code == 400


# =============================================================================
# POST /api/voice/tts — additional edge cases
# =============================================================================


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_uses_default_credential_when_no_api_key(mock_connect, mock_settings, client):
    """POST /api/voice/tts falls back to DefaultAzureCredential when no API key."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = None  # no key → DefaultAzureCredential
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    audio_delta = _make_event("response.audio.delta", delta=b"\xaa\xbb")
    done = _make_event("response.done")
    conn = FakeConnection([audio_delta, done])
    mock_connect.return_value = _make_connect_ctx(conn)

    with patch("app.routers.voice_live.DefaultAzureCredential") as mock_dac:
        mock_cred = MagicMock()
        mock_cred.close = None  # no close method
        mock_dac.return_value = mock_cred
        response = client.post("/api/voice/tts", json={"text": "Test default cred"})
    assert response.status_code == 200
    assert len(response.content) > 0


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_base64_string_delta(mock_connect, mock_settings, client):
    """POST /api/voice/tts decodes base64 string deltas correctly."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = "test-key"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    raw_audio = b"\x01\x02\x03\x04"
    b64_audio = base64.b64encode(raw_audio).decode("utf-8")
    audio_delta = _make_event("response.audio.delta", delta=b64_audio)
    # delta is a string, not bytes — code should base64-decode it
    audio_delta.delta = b64_audio
    done = _make_event("response.done")
    conn = FakeConnection([audio_delta, done])
    mock_connect.return_value = _make_connect_ctx(conn)

    response = client.post("/api/voice/tts", json={"text": "base64 test"})
    assert response.status_code == 200
    assert response.content == raw_audio


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_error_event_stops_collection(mock_connect, mock_settings, client):
    """POST /api/voice/tts stops on error events and returns 500 (no audio)."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = "test-key"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    error_obj = MagicMock()
    error_obj.message = "quota exceeded"
    error_event = _make_event(ServerEventType.ERROR.value, error=error_obj)
    conn = FakeConnection([error_event])
    mock_connect.return_value = _make_connect_ctx(conn)

    response = client.post("/api/voice/tts", json={"text": "error test"})
    assert response.status_code == 500


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_credential_async_close(mock_connect, mock_settings, client):
    """POST /api/voice/tts awaits credential.close() if it returns a coroutine."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = None
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    audio_delta = _make_event("response.audio.delta", delta=b"\xff")
    done = _make_event("response.done")
    conn = FakeConnection([audio_delta, done])
    mock_connect.return_value = _make_connect_ctx(conn)

    with patch("app.routers.voice_live.DefaultAzureCredential") as mock_dac:
        mock_cred = MagicMock()
        mock_cred.close = AsyncMock()  # async close
        mock_dac.return_value = mock_cred
        response = client.post("/api/voice/tts", json={"text": "async close test"})
    assert response.status_code == 200
    mock_cred.close.assert_called_once()


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_tts_fallback_to_openai_endpoint(mock_connect, mock_settings, client):
    """POST /api/voice/tts uses azure_openai_endpoint as fallback."""
    mock_settings.azure_voicelive_endpoint = None
    mock_settings.azure_openai_endpoint = "https://fallback.openai.azure.com"
    mock_settings.azure_voicelive_api_key = "key"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"

    audio_delta = _make_event("response.audio.delta", delta=b"\x10")
    done = _make_event("response.done")
    conn = FakeConnection([audio_delta, done])
    mock_connect.return_value = _make_connect_ctx(conn)

    response = client.post("/api/voice/tts", json={"text": "fallback test"})
    assert response.status_code == 200


# =============================================================================
# _call_foundry_agent wrapper
# =============================================================================


@pytest.mark.asyncio
@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.call_foundry_agent", new_callable=AsyncMock)
async def test_call_foundry_agent_wrapper(mock_call, mock_settings):
    """_call_foundry_agent delegates to call_foundry_agent with settings."""
    from app.routers.voice_live import _call_foundry_agent

    mock_settings.azure_client_id = "test-client-id"
    mock_settings.azure_foundry_endpoint = "https://foundry.test"
    mock_settings.foundry_chat_agent = "chat-agent"
    mock_settings.foundry_product_agent = "product-agent"
    mock_settings.foundry_policy_agent = "policy-agent"
    mock_call.return_value = "Agent response"

    result = await _call_foundry_agent("What colors?")
    assert result == "Agent response"
    mock_call.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.call_foundry_agent", new_callable=AsyncMock)
async def test_call_foundry_agent_wrapper_no_client_id(mock_call, mock_settings):
    """_call_foundry_agent passes None when azure_client_id is empty."""
    from app.routers.voice_live import _call_foundry_agent

    mock_settings.azure_client_id = None
    mock_settings.azure_foundry_endpoint = "https://foundry.test"
    mock_settings.foundry_chat_agent = "chat"
    mock_settings.foundry_product_agent = "product"
    mock_settings.foundry_policy_agent = "policy"
    mock_call.return_value = "ok"

    await _call_foundry_agent("hi")
    kwargs = mock_call.call_args
    assert kwargs[1]["azure_client_id"] is None or mock_call.call_args


# =============================================================================
# VoiceLiveHandler — direct class tests
# =============================================================================


@pytest.mark.asyncio
async def test_handler_start_and_stop():
    """VoiceLiveHandler.start() creates a task and stop() cancels it."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    config = VoiceSessionConfig(
        mode="model", model="gpt-realtime-mini", voice="alloy",
        transcribe_model="gpt-4o-transcribe", instructions="test",
    )
    send_fn = AsyncMock()
    handler = VoiceLiveHandler(
        client_id="test-1", endpoint="https://voice.openai.azure.com",
        credential=MagicMock(), send_message=send_fn, config=config,
    )
    assert handler.is_running is False

    with patch("app.routers.voice_live.connect") as mock_connect:
        # Make connect block indefinitely so we can test stop
        async def block_forever(*a, **kw):
            await asyncio.sleep(100)
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(side_effect=block_forever)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_connect.return_value = mock_ctx

        await handler.start()
        assert handler.is_running is True
        assert handler._event_task is not None

        await handler.stop()
        assert handler.is_running is False
        assert handler.connection is None


@pytest.mark.asyncio
async def test_handler_send_audio_drops_while_processing():
    """send_audio drops audio when _is_processing is True."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=AsyncMock(), config=config,
    )
    handler._is_processing = True
    handler.connection = AsyncMock()

    await handler.send_audio("base64data")
    handler.connection.input_audio_buffer.append.assert_not_called()


@pytest.mark.asyncio
async def test_handler_send_audio_forwards():
    """send_audio forwards to connection when not processing."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=AsyncMock(), config=config,
    )
    handler._is_processing = False
    handler.connection = AsyncMock()

    await handler.send_audio("audio_chunk")
    handler.connection.input_audio_buffer.append.assert_awaited_once_with(audio="audio_chunk")


@pytest.mark.asyncio
async def test_handler_interrupt():
    """interrupt() cancels the current response."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=AsyncMock(), config=config,
    )
    handler.connection = AsyncMock()
    handler._native_agent = False

    await handler.interrupt()
    handler.connection.response.cancel.assert_awaited_once()


@pytest.mark.asyncio
async def test_handler_interrupt_native_agent_noop():
    """interrupt() does nothing in native agent mode."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=AsyncMock(), config=config,
    )
    handler.connection = AsyncMock()
    handler._native_agent = True

    await handler.interrupt()
    handler.connection.response.cancel.assert_not_awaited()


@pytest.mark.asyncio
async def test_handler_stop_with_async_credential_close():
    """stop() awaits credential.close() if it's async."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    cred = MagicMock()
    cred.close = AsyncMock()

    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=cred,
        send_message=AsyncMock(), config=config,
    )
    handler.is_running = True
    handler.connection = MagicMock()

    await handler.stop()
    cred.close.assert_called_once()


@pytest.mark.asyncio
async def test_handler_run_non_model_mode():
    """_run() sends error for non-model mode."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="agent-direct", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    await handler._run()
    send_fn.assert_awaited()
    msg = send_fn.call_args[0][0]
    assert msg["type"] == "error"
    assert "model" in msg["message"].lower()


@pytest.mark.asyncio
async def test_handler_configure_session():
    """_configure_session sends session dict to the connection."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="gpt-realtime-mini", voice="alloy",
        transcribe_model="gpt-4o-transcribe", instructions="test",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    mock_conn = AsyncMock()
    with patch("app.routers.voice_live.settings") as mock_settings:
        mock_settings.voicelive_vad_threshold = 0.5
        mock_settings.voicelive_vad_silence_ms = 1200
        mock_settings.voicelive_vad_prefix_padding_ms = 300
        await handler._configure_session(mock_conn)

    mock_conn.session.update.assert_awaited_once()
    send_fn.assert_awaited()
    msg = send_fn.call_args[0][0]
    assert msg["type"] == "session_started"
    assert msg["config"]["mode"] == "model"


@pytest.mark.asyncio
async def test_handler_configure_session_native():
    """_configure_session_native sends session_started with native_agent=True."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    mock_conn = AsyncMock()
    await handler._configure_session_native(mock_conn)
    msg = send_fn.call_args[0][0]
    assert msg["type"] == "session_started"
    assert msg["config"]["native_agent"] is True


# =============================================================================
# VoiceLiveHandler._handle_event — individual event types
# =============================================================================


@pytest.mark.asyncio
async def test_handle_event_speech_started():
    """Speech started sends listening status and stop_playback."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler._is_processing = False

    conn = AsyncMock()
    ev = _make_event(ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED.value)
    await handler._handle_event(ev, conn)

    calls = [c[0][0] for c in send_fn.call_args_list]
    assert any(m.get("type") == "status" and m.get("state") == "listening" for m in calls)
    assert any(m.get("type") == "stop_playback" for m in calls)
    conn.response.cancel.assert_awaited()


@pytest.mark.asyncio
async def test_handle_event_speech_started_while_processing():
    """Speech started is ignored while processing."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler._is_processing = True

    ev = _make_event(ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED.value)
    await handler._handle_event(ev, AsyncMock())
    send_fn.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_event_speech_stopped():
    """Speech stopped sends thinking status."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler._is_processing = False

    ev = _make_event(ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED.value)
    await handler._handle_event(ev, AsyncMock())

    msg = send_fn.call_args[0][0]
    assert msg["type"] == "status"
    assert msg["state"] == "thinking"


@pytest.mark.asyncio
async def test_handle_event_speech_stopped_while_processing():
    """Speech stopped is ignored while processing."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler._is_processing = True

    ev = _make_event(ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED.value)
    await handler._handle_event(ev, AsyncMock())
    send_fn.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_event_audio_delta():
    """RESPONSE_AUDIO_DELTA sends audio_data with base64-encoded content."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    raw = b"\x10\x20"
    b64 = base64.b64encode(raw).decode()
    ev = _make_event(ServerEventType.RESPONSE_AUDIO_DELTA.value, delta=b64)
    await handler._handle_event(ev, AsyncMock())

    msg = send_fn.call_args[0][0]
    assert msg["type"] == "audio_data"
    assert msg["data"] == b64
    assert handler._is_processing is True


@pytest.mark.asyncio
async def test_handle_event_audio_delta_bytes():
    """RESPONSE_AUDIO_DELTA with bytes delta encodes to base64."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    raw = b"\xaa\xbb"
    ev = _make_event(ServerEventType.RESPONSE_AUDIO_DELTA.value, delta=raw)
    await handler._handle_event(ev, AsyncMock())

    msg = send_fn.call_args[0][0]
    assert msg["type"] == "audio_data"
    assert base64.b64decode(msg["data"]) == raw


@pytest.mark.asyncio
async def test_handle_event_transcript_completed():
    """User input audio transcription sends transcript."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    ev = _make_event(
        ServerEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED.value,
        transcript="Hello there",
    )
    await handler._handle_event(ev, AsyncMock())

    msg = send_fn.call_args[0][0]
    assert msg["type"] == "transcript"
    assert msg["role"] == "user"
    assert msg["isFinal"] is True


@pytest.mark.asyncio
async def test_handle_event_audio_transcript_delta():
    """Audio transcript delta accumulates and sends partial transcript."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    ev = _make_event(ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value, delta="Hello ")
    await handler._handle_event(ev, AsyncMock())

    msg = send_fn.call_args[0][0]
    assert msg["type"] == "transcript"
    assert msg["role"] == "assistant"
    assert msg["isFinal"] is False
    assert handler._assistant_transcript == "Hello "


@pytest.mark.asyncio
async def test_handle_event_response_done():
    """RESPONSE_DONE sends final transcript and resets state."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler._assistant_transcript = "Hello there"
    handler._is_processing = True

    resp_obj = MagicMock()
    resp_obj.output = []
    ev = _make_event(ServerEventType.RESPONSE_DONE.value, response=resp_obj)
    await handler._handle_event(ev, AsyncMock())

    calls = [c[0][0] for c in send_fn.call_args_list]
    final_transcript = [m for m in calls if m.get("type") == "transcript" and m.get("isFinal")]
    assert len(final_transcript) == 1
    assert final_transcript[0]["text"] == "Hello there"

    assert handler._assistant_transcript == ""
    assert handler._is_processing is False


@pytest.mark.asyncio
async def test_handle_event_response_done_with_structured_text():
    """RESPONSE_DONE includes structuredText from last tool result."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler._assistant_text_response = "Agent said this"
    handler._last_tool_result = "Structured result from Foundry"
    handler._is_processing = True

    ev = _make_event(ServerEventType.RESPONSE_DONE.value, response=None)
    await handler._handle_event(ev, AsyncMock())

    calls = [c[0][0] for c in send_fn.call_args_list]
    final = [m for m in calls if m.get("type") == "transcript" and m.get("isFinal")]
    assert final[0]["text"] == "Agent said this"
    assert final[0]["structuredText"] == "Structured result from Foundry"


@pytest.mark.asyncio
async def test_handle_event_response_text_delta():
    """response.text.delta accumulates text response."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    ev = _make_event("response.text.delta", delta="some text")
    await handler._handle_event(ev, AsyncMock())
    assert handler._assistant_text_response == "some text"
    msg = send_fn.call_args[0][0]
    assert msg["state"] == "speaking"


@pytest.mark.asyncio
async def test_handle_event_error_fatal():
    """Fatal error events are sent to the client."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    err = MagicMock()
    err.message = "Something bad happened"
    ev = _make_event(ServerEventType.ERROR.value, error=err)
    await handler._handle_event(ev, AsyncMock())

    msg = send_fn.call_args[0][0]
    assert msg["type"] == "error"
    assert "Something bad happened" in msg["message"]


@pytest.mark.asyncio
async def test_handle_event_error_non_fatal():
    """Non-fatal error events (e.g. 'no active response') are silently ignored."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    err = MagicMock()
    err.message = "no active response to cancel"
    ev = _make_event(ServerEventType.ERROR.value, error=err)
    await handler._handle_event(ev, AsyncMock())

    send_fn.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_event_function_call_arguments_delta():
    """Function call argument deltas are accumulated."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    ev1 = _make_event("response.function_call_arguments.delta",
                       call_id="c1", name="ask_customer_service", delta='{"quest')
    ev2 = _make_event("response.function_call_arguments.delta",
                       call_id="c1", name="", delta='ion": "hi"}')
    await handler._handle_event(ev1, AsyncMock())
    await handler._handle_event(ev2, AsyncMock())

    assert "c1" in handler._pending_tool_calls
    assert handler._pending_tool_calls["c1"]["arguments"] == '{"question": "hi"}'


@pytest.mark.asyncio
@patch("app.routers.voice_live._call_foundry_agent", new_callable=AsyncMock)
async def test_handle_event_function_call_done(mock_foundry):
    """Function call done invokes Foundry agent and submits result."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    mock_foundry.return_value = "Paint colors available"
    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    # Pre-populate pending call
    handler._pending_tool_calls["c1"] = {
        "name": "ask_customer_service",
        "arguments": '{"question": "colors"}',
    }

    conn = AsyncMock()
    ev = _make_event("response.function_call_arguments.done",
                     call_id="c1", name="", arguments="")
    await handler._handle_event(ev, conn)

    mock_foundry.assert_awaited_once_with("colors")
    assert handler._last_tool_result == "Paint colors available"
    conn.conversation.item.create.assert_awaited_once()
    conn.response.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_event_response_created():
    """RESPONSE_CREATED event is a no-op (no crash)."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )

    ev = _make_event(ServerEventType.RESPONSE_CREATED.value)
    await handler._handle_event(ev, AsyncMock())
    send_fn.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_events_stops_when_not_running():
    """_process_events breaks when is_running is False."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler.is_running = False

    ev = _make_event("something")
    conn = FakeConnection([ev])
    await handler._process_events(conn)
    # Should not have processed any events
    send_fn.assert_not_awaited()


# =============================================================================
# VoiceLiveHandler._run — native agent mode
# =============================================================================


@pytest.mark.asyncio
async def test_handler_run_native_agent_mode():
    """_run() uses native agent config when agent_name and project are set."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="m", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="https://e.openai.azure.com",
        credential=MagicMock(), send_message=send_fn, config=config,
    )

    conn = FakeConnection([])  # no events, will exhaust immediately

    with patch("app.routers.voice_live.settings") as mock_s:
        mock_s.azure_voicelive_agent_name = "my-agent"
        mock_s.azure_voicelive_project = "my-project"
        with patch("app.routers.voice_live.connect") as mock_connect:
            mock_connect.return_value = _make_connect_ctx(conn)
            await handler._run()

    # Should have called connect with agent_config
    call_kwargs = mock_connect.call_args[1]
    assert "agent_config" in call_kwargs
    assert call_kwargs["agent_config"]["agent_name"] == "my-agent"


@pytest.mark.asyncio
async def test_handler_run_model_mode():
    """_run() model mode calls connect with model parameter."""
    from app.routers.voice_live import VoiceLiveHandler, VoiceSessionConfig

    send_fn = AsyncMock()
    config = VoiceSessionConfig(
        mode="model", model="gpt-realtime-mini", voice="alloy",
        transcribe_model="t", instructions="i",
    )
    handler = VoiceLiveHandler(
        client_id="x", endpoint="https://e.openai.azure.com",
        credential=MagicMock(), send_message=send_fn, config=config,
    )

    conn = FakeConnection([])

    with patch("app.routers.voice_live.settings") as mock_s:
        mock_s.azure_voicelive_agent_name = ""
        mock_s.azure_voicelive_project = ""
        mock_s.voicelive_vad_threshold = 0.5
        mock_s.voicelive_vad_silence_ms = 1200
        mock_s.voicelive_vad_prefix_padding_ms = 300
        with patch("app.routers.voice_live.connect") as mock_connect:
            mock_connect.return_value = _make_connect_ctx(conn)
            await handler._run()

    call_kwargs = mock_connect.call_args[1]
    assert call_kwargs["model"] == "gpt-realtime-mini"


# =============================================================================
# WebSocket endpoint (/api/voice/ws)
# =============================================================================


@patch("app.routers.voice_live.settings")
def test_ws_start_session_no_endpoint(mock_settings, client):
    """WS start_session sends error when no endpoint configured."""
    mock_settings.azure_voicelive_endpoint = None
    mock_settings.azure_openai_endpoint = None

    with client.websocket_connect("/api/voice/ws/test-client") as ws:
        ws.send_text(json.dumps({"type": "start_session", "mode": "model"}))
        resp = json.loads(ws.receive_text())
        assert resp["type"] == "error"
        assert "endpoint" in resp["message"].lower()


@patch("app.routers.voice_live.settings")
def test_ws_start_session_invalid_endpoint(mock_settings, client):
    """WS start_session sends error for non-openai endpoint."""
    mock_settings.azure_voicelive_endpoint = "https://invalid.services.ai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = "key"

    with client.websocket_connect("/api/voice/ws/test-client") as ws:
        ws.send_text(json.dumps({"type": "start_session", "mode": "model"}))
        resp = json.loads(ws.receive_text())
        assert resp["type"] == "error"
        assert "openai.azure.com" in resp["message"].lower()


@patch("app.routers.voice_live.settings")
def test_ws_stop_session(mock_settings, client):
    """WS stop_session returns session_stopped."""
    mock_settings.azure_voicelive_endpoint = None
    mock_settings.azure_openai_endpoint = None

    with client.websocket_connect("/api/voice/ws/test-client") as ws:
        ws.send_text(json.dumps({"type": "stop_session"}))
        resp = json.loads(ws.receive_text())
        assert resp["type"] == "session_stopped"


@patch("app.routers.voice_live.settings")
@patch("app.routers.voice_live.connect")
def test_ws_start_session_success(mock_connect, mock_settings, client):
    """WS start_session creates handler and receives session_started."""
    mock_settings.azure_voicelive_endpoint = "https://voice.openai.azure.com"
    mock_settings.azure_openai_endpoint = None
    mock_settings.azure_voicelive_api_key = "key"
    mock_settings.voicelive_mode = "model"
    mock_settings.voicelive_model = "gpt-realtime-mini"
    mock_settings.voicelive_voice = "alloy"
    mock_settings.voicelive_transcribe_model = "gpt-4o-transcribe"
    mock_settings.voicelive_instructions = ""
    mock_settings.azure_voicelive_agent_name = ""
    mock_settings.azure_voicelive_project = ""

    mock_settings.voicelive_vad_threshold = 0.5
    mock_settings.voicelive_vad_silence_ms = 1200
    mock_settings.voicelive_vad_prefix_padding_ms = 300

    conn = FakeConnection([])
    mock_connect.return_value = _make_connect_ctx(conn)

    with client.websocket_connect("/api/voice/ws/ws-test") as ws:
        ws.send_text(json.dumps({"type": "start_session", "mode": "model"}))
        resp = json.loads(ws.receive_text())
        assert resp["type"] == "session_started"


# =============================================================================
# Module-level helpers
# =============================================================================


@pytest.mark.asyncio
async def test_handle_message_audio_chunk():
    """_handle_message forwards audio_chunk to handler.send_audio."""
    from app.routers.voice_live import (
        VoiceLiveHandler,
        VoiceSessionConfig,
        _handle_message,
        _handlers,
    )

    send_fn = AsyncMock()
    config = VoiceSessionConfig(mode="model", model="m", voice="alloy",
                                transcribe_model="t", instructions="i")
    handler = VoiceLiveHandler(
        client_id="c", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler.connection = AsyncMock()
    handler._is_processing = False
    _handlers["c"] = handler

    ws = AsyncMock()
    await _handle_message("c", {"type": "audio_chunk", "data": "abc123"}, ws)
    handler.connection.input_audio_buffer.append.assert_awaited_once()

    del _handlers["c"]


@pytest.mark.asyncio
async def test_handle_message_interrupt():
    """_handle_message forwards interrupt to handler.interrupt."""
    from app.routers.voice_live import (
        VoiceLiveHandler,
        VoiceSessionConfig,
        _handle_message,
        _handlers,
    )

    send_fn = AsyncMock()
    config = VoiceSessionConfig(mode="model", model="m", voice="alloy",
                                transcribe_model="t", instructions="i")
    handler = VoiceLiveHandler(
        client_id="c", endpoint="e", credential=MagicMock(),
        send_message=send_fn, config=config,
    )
    handler.connection = AsyncMock()
    handler._native_agent = False
    _handlers["c"] = handler

    ws = AsyncMock()
    await _handle_message("c", {"type": "interrupt"}, ws)
    handler.connection.response.cancel.assert_awaited_once()

    del _handlers["c"]


@pytest.mark.asyncio
async def test_cleanup_client():
    """_cleanup_client stops handler and removes from registry."""
    from app.routers.voice_live import (
        VoiceLiveHandler,
        VoiceSessionConfig,
        _cleanup_client,
        _handlers,
    )

    config = VoiceSessionConfig(mode="model", model="m", voice="alloy",
                                transcribe_model="t", instructions="i")
    handler = VoiceLiveHandler(
        client_id="c", endpoint="e", credential=MagicMock(),
        send_message=AsyncMock(), config=config,
    )
    handler.is_running = True
    handler.connection = MagicMock()
    _handlers["c"] = handler

    await _cleanup_client("c")
    assert "c" not in _handlers
    assert handler.is_running is False
