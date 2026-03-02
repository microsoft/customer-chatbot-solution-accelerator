import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import (
    AudioInputTranscriptionOptions,
    AzureStandardVoice,
    InputAudioFormat,
    Modality,
    OutputAudioFormat,
    RequestSession,
    ServerVad,
    ServerEventType,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

try:
    from ..config import settings
except ImportError:
    from app.config import settings


router = APIRouter(prefix="/api/voice", tags=["voice-live"])
logger = logging.getLogger(__name__)


@dataclass
class VoiceSessionConfig:
    mode: str
    model: str
    voice: str
    transcribe_model: str
    instructions: str


class VoiceLiveHandler:
    def __init__(
        self,
        client_id: str,
        endpoint: str,
        credential: Any,
        send_message,
        config: VoiceSessionConfig,
    ):
        self.client_id = client_id
        self.endpoint = endpoint
        self.credential = credential
        self.send = send_message
        self.config = config
        self.connection = None
        self.is_running = False
        self._event_task: Optional[asyncio.Task] = None
        self._assistant_transcript = ""
        self._audio_chunks_sent = 0

    async def start(self) -> None:
        self.is_running = True
        self._event_task = asyncio.create_task(self._run())

    async def send_audio(self, audio_base64: str) -> None:
        if self.connection and audio_base64:
            try:
                await self.connection.input_audio_buffer.append(audio=audio_base64)
                self._audio_chunks_sent += 1
                if self._audio_chunks_sent == 1 or self._audio_chunks_sent % 100 == 0:
                    logger.info(
                        "[%s] Forwarded audio chunks: %s",
                        self.client_id,
                        self._audio_chunks_sent,
                    )
            except Exception as exc:
                logger.error("[%s] Error forwarding audio: %s", self.client_id, exc)

    async def interrupt(self) -> None:
        if self.connection:
            try:
                await self.connection.response.cancel()
            except Exception as exc:
                logger.debug("[%s] No response to cancel: %s", self.client_id, exc)

    async def stop(self) -> None:
        self.is_running = False
        if self._event_task and not self._event_task.done():
            self._event_task.cancel()
            try:
                await self._event_task
            except (asyncio.CancelledError, Exception):
                pass
        self.connection = None
        close_fn = getattr(self.credential, "close", None)
        if callable(close_fn):
            result = close_fn()
            if asyncio.iscoroutine(result):
                await result

    async def _run(self) -> None:
        try:
            if self.config.mode != "model":
                await self.send(
                    {
                        "type": "error",
                        "message": "Only 'model' mode is currently enabled in this app.",
                    }
                )
                return

            async with connect(
                endpoint=self.endpoint,
                credential=self.credential,
                model=self.config.model,
            ) as connection:
                self.connection = connection
                await self._configure_session(connection)
                await self._process_events(connection)
        except Exception as exc:
            logger.error("[%s] Voice Live error: %s", self.client_id, exc)
            await self.send({"type": "error", "message": str(exc)})

    def _resolve_voice(self) -> Any:
        voice_name = (self.config.voice or "").strip()
        if not voice_name:
            return None

        realtime_voices = {
            "alloy",
            "ash",
            "ballad",
            "coral",
            "echo",
            "sage",
            "shimmer",
            "verse",
        }

        if voice_name.lower() in realtime_voices:
            return voice_name

        return AzureStandardVoice(name=voice_name)

    async def _configure_session(self, connection) -> None:
        voice_config = self._resolve_voice()
        session = RequestSession(
            modalities=[Modality.TEXT, Modality.AUDIO],
            voice=voice_config,
            instructions=self.config.instructions,
            input_audio_format=InputAudioFormat.PCM16,
            output_audio_format=OutputAudioFormat.PCM16,
            turn_detection=ServerVad(
                create_response=True,
                interrupt_response=True,
                auto_truncate=True,
                threshold=0.5,
                silence_duration_ms=500,
                prefix_padding_ms=300,
            ),
            input_audio_transcription=AudioInputTranscriptionOptions(
                model=self.config.transcribe_model
            ),
        )
        await connection.session.update(session=session)
        await self.send(
            {
                "type": "session_started",
                "config": {
                    "mode": self.config.mode,
                    "model": self.config.model,
                    "voice": self.config.voice,
                    "transcribe_model": self.config.transcribe_model,
                },
            }
        )

    async def _process_events(self, connection) -> None:
        async for event in connection:
            if not self.is_running:
                break
            try:
                await self._handle_event(event, connection)
            except Exception as exc:
                logger.error("[%s] Event handling error: %s", self.client_id, exc)

    async def _handle_event(self, event, connection) -> None:
        raw_event_type = getattr(event, "type", None)
        event_type = getattr(raw_event_type, "value", raw_event_type)
        logger.debug("[%s] Voice event: %s", self.client_id, event_type)

        if event_type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STARTED.value:
            await self.send({"type": "status", "state": "listening"})
            await self.send({"type": "stop_playback"})
            try:
                await connection.response.cancel()
            except Exception:
                pass

        elif event_type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED.value:
            await self.send({"type": "status", "state": "thinking"})

        elif event_type == ServerEventType.RESPONSE_CREATED.value:
            await self.send({"type": "status", "state": "speaking"})

        elif event_type == ServerEventType.RESPONSE_AUDIO_DELTA.value:
            delta = getattr(event, "delta", None)
            if delta:
                if isinstance(delta, str):
                    audio_b64 = delta
                else:
                    audio_b64 = base64.b64encode(delta).decode("utf-8")
                await self.send(
                    {
                        "type": "audio_data",
                        "data": audio_b64,
                        "format": "pcm16",
                        "sampleRate": 24000,
                        "channels": 1,
                    }
                )

        elif (
            event_type
            == ServerEventType.CONVERSATION_ITEM_INPUT_AUDIO_TRANSCRIPTION_COMPLETED.value
        ):
            transcript = getattr(event, "transcript", "")
            if transcript:
                await self.send(
                    {
                        "type": "transcript",
                        "role": "user",
                        "text": transcript,
                        "isFinal": True,
                    }
                )

        elif event_type == ServerEventType.RESPONSE_AUDIO_TRANSCRIPT_DELTA.value:
            delta_text = getattr(event, "delta", "")
            if delta_text:
                self._assistant_transcript += delta_text
                await self.send(
                    {
                        "type": "transcript",
                        "role": "assistant",
                        "text": self._assistant_transcript,
                        "isFinal": False,
                    }
                )

        elif event_type == ServerEventType.RESPONSE_DONE.value:
            if self._assistant_transcript:
                await self.send(
                    {
                        "type": "transcript",
                        "role": "assistant",
                        "text": self._assistant_transcript,
                        "isFinal": True,
                    }
                )
                self._assistant_transcript = ""
            await self.send({"type": "status", "state": "listening"})

        elif event_type == ServerEventType.ERROR.value:
            error_obj = getattr(event, "error", None)
            message = getattr(error_obj, "message", str(error_obj or event))
            await self.send({"type": "error", "message": message})


_handlers: Dict[str, VoiceLiveHandler] = {}


@router.get("/config")
async def get_voice_config():
    return {
        "enabled": bool(settings.azure_voicelive_endpoint or settings.azure_openai_endpoint),
        "mode": settings.voicelive_mode,
        "model": settings.voicelive_model,
        "voice": settings.voicelive_voice,
        "transcribe_model": settings.voicelive_transcribe_model,
        "instructions": settings.voicelive_instructions,
    }


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await _handle_message(client_id, message, websocket)
    except WebSocketDisconnect:
        logger.info("Voice client disconnected: %s", client_id)
    except Exception as exc:
        logger.error("Voice websocket error for %s: %s", client_id, exc)
    finally:
        await _cleanup_client(client_id)


async def _handle_message(client_id: str, message: dict, websocket: WebSocket):
    msg_type = message.get("type")

    if msg_type == "start_session":
        config = {k: v for k, v in message.items() if k != "type"}
        await _start_session(client_id, config, websocket)

    elif msg_type == "stop_session":
        await _stop_session(client_id, websocket)

    elif msg_type == "audio_chunk":
        handler = _handlers.get(client_id)
        if handler:
            await handler.send_audio(message.get("data", ""))

    elif msg_type == "interrupt":
        handler = _handlers.get(client_id)
        if handler:
            await handler.interrupt()


async def _start_session(client_id: str, config: dict, websocket: WebSocket):
    endpoint = settings.azure_voicelive_endpoint or settings.azure_openai_endpoint
    if not endpoint:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "message": "Missing realtime endpoint. Set AZURE_OPENAI_ENDPOINT (preferred) or AZURE_VOICELIVE_ENDPOINT.",
                }
            )
        )
        return

    endpoint_host = endpoint.lower()
    if "services.ai.azure.com" in endpoint_host and settings.azure_openai_endpoint:
        endpoint = settings.azure_openai_endpoint
        endpoint_host = endpoint.lower()

    if "openai.azure.com" not in endpoint_host:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "message": "Realtime websocket requires an Azure OpenAI endpoint host (*.openai.azure.com).",
                }
            )
        )
        return

    credential: Any
    if settings.azure_voicelive_api_key:
        credential = AzureKeyCredential(settings.azure_voicelive_api_key)
    else:
        credential = DefaultAzureCredential()

    async def send_to_client(msg: dict):
        await websocket.send_text(json.dumps(msg))

    session_config = VoiceSessionConfig(
        mode=config.get("mode", settings.voicelive_mode),
        model=config.get("model", settings.voicelive_model),
        voice=config.get("voice", settings.voicelive_voice),
        transcribe_model=config.get(
            "transcribe_model", settings.voicelive_transcribe_model
        ),
        instructions=config.get("instructions", settings.voicelive_instructions),
    )

    handler = VoiceLiveHandler(
        client_id=client_id,
        endpoint=endpoint,
        credential=credential,
        send_message=send_to_client,
        config=session_config,
    )

    previous_handler = _handlers.get(client_id)
    if previous_handler:
        await previous_handler.stop()

    _handlers[client_id] = handler
    await handler.start()


async def _stop_session(client_id: str, websocket: WebSocket):
    handler = _handlers.pop(client_id, None)
    if handler:
        await handler.stop()
    await websocket.send_text(json.dumps({"type": "session_stopped"}))


async def _cleanup_client(client_id: str):
    handler = _handlers.pop(client_id, None)
    if handler:
        await handler.stop()
