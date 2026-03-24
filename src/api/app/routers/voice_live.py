import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from azure.ai.voicelive.aio import connect
from azure.ai.voicelive.models import (
    AudioInputTranscriptionOptions,
    FunctionTool,
    InputAudioFormat,
    Modality,
    OutputAudioFormat,
    RequestSession,
    ServerEventType,
    ServerVad,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.requests import Request
from fastapi.responses import Response

try:
    from ..config import settings
    from ..utils.foundry_agent_utils import call_foundry_agent
    from ..utils.voice_utils import (
        clean_text_for_speech,
        is_valid_realtime_endpoint,
        resolve_credential,
        resolve_endpoint,
        resolve_voice,
    )
except ImportError:
    from app.config import settings
    from app.utils.foundry_agent_utils import call_foundry_agent
    from app.utils.voice_utils import (
        clean_text_for_speech,
        is_valid_realtime_endpoint,
        resolve_credential,
        resolve_endpoint,
        resolve_voice,
    )


router = APIRouter(prefix="/api/voice", tags=["voice-live"])
logger = logging.getLogger(__name__)


# ── Foundry agent tool: routes voice questions through the same pipeline as text ──

FOUNDRY_AGENT_TOOL = FunctionTool(
    name="ask_customer_service",
    description=(
        "Ask the Contoso Paint Company customer service system a question. "
        "This searches enterprise data for products, policies, returns, warranties, "
        "color matching, and any company information. Use this for ANY customer question."
    ),
    parameters={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The customer's question to answer",
            },
        },
        "required": ["question"],
    },
)

VOICE_TOOLS: list = [FOUNDRY_AGENT_TOOL]

GROUNDING_INSTRUCTIONS = (
    "You are a voice interface for the Contoso Paint Company customer service system. "
    "You MUST call the ask_customer_service function for EVERY customer question "
    "to get accurate, grounded answers from the company knowledge base.\n\n"
    "RULES:\n"
    "- ALWAYS call ask_customer_service before answering any question about products, "
    "policies, returns, warranties, colors, prices, or services.\n"
    "- Read back the answer naturally in a conversational tone.\n"
    "- Do NOT make up information. Only use what the function returns.\n"
    "- If the function returns no results, tell the customer honestly.\n"
    "- For greetings and small talk, you can respond directly without calling the function."
)


async def _call_foundry_agent(question: str) -> str:
    """Delegate to foundry_agent_utils."""
    client_id = str(settings.azure_client_id) if settings.azure_client_id else None
    return await call_foundry_agent(
        question=question,
        foundry_endpoint=settings.azure_foundry_endpoint or "",
        chat_agent_name=settings.foundry_chat_agent,
        product_agent_name=settings.foundry_product_agent,
        policy_agent_name=settings.foundry_policy_agent,
        azure_client_id=client_id,
    )


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
        self._pending_tool_calls: Dict[str, dict] = {}
        self._is_processing = False  # Guard against overlapping requests

    async def start(self) -> None:
        self.is_running = True
        self._event_task = asyncio.create_task(self._run())

    async def send_audio(self, audio_base64: str) -> None:
        # Drop audio while processing or agent is speaking to prevent feedback
        if self._is_processing:
            return
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
        return resolve_voice(self.config.voice)

    async def _configure_session(self, connection) -> None:
        voice_config = self._resolve_voice()
        session = RequestSession(
            modalities=[Modality.TEXT, Modality.AUDIO],
            voice=voice_config,
            instructions=GROUNDING_INSTRUCTIONS,
            input_audio_format=InputAudioFormat.PCM16,
            output_audio_format=OutputAudioFormat.PCM16,
            turn_detection=ServerVad(
                create_response=True,
                interrupt_response=True,
                auto_truncate=True,
                threshold=settings.voicelive_vad_threshold,
                silence_duration_ms=settings.voicelive_vad_silence_ms,
                prefix_padding_ms=settings.voicelive_vad_prefix_padding_ms,
            ),
            input_audio_transcription=AudioInputTranscriptionOptions(
                model=self.config.transcribe_model,
                language="en",
            ),
            tools=VOICE_TOOLS,
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
            # Ignore new speech if we're still processing the previous request
            if self._is_processing:
                logger.info("[%s] Ignoring speech_started — still processing previous request", self.client_id)
                return
            await self.send({"type": "status", "state": "listening"})
            await self.send({"type": "stop_playback"})
            try:
                await connection.response.cancel()
            except Exception:
                pass

        elif event_type == ServerEventType.INPUT_AUDIO_BUFFER_SPEECH_STOPPED.value:
            if self._is_processing:
                logger.info("[%s] Ignoring speech_stopped — still processing", self.client_id)
                return
            await self.send({"type": "status", "state": "thinking"})

        # ── Function call handling (enterprise grounding) ──
        elif event_type == "response.function_call_arguments.delta":
            call_id = getattr(event, "call_id", None)
            delta = getattr(event, "delta", "")
            if call_id:
                if call_id not in self._pending_tool_calls:
                    self._pending_tool_calls[call_id] = {
                        "name": getattr(event, "name", ""),
                        "arguments": "",
                    }
                self._pending_tool_calls[call_id]["arguments"] += delta

        elif event_type == "response.function_call_arguments.done":
            call_id = getattr(event, "call_id", None)
            name = getattr(event, "name", "")
            arguments_str = getattr(event, "arguments", "")

            if call_id and call_id in self._pending_tool_calls:
                pending = self._pending_tool_calls.pop(call_id)
                if not name:
                    name = pending.get("name", "")
                if not arguments_str:
                    arguments_str = pending.get("arguments", "")

            logger.info("[%s] Function call: %s(%s)", self.client_id, name, arguments_str)
            self._is_processing = True
            await self.send({"type": "status", "state": "thinking"})

            result_text = ""
            try:
                args = json.loads(arguments_str) if arguments_str else {}
                question = args.get("question", "")
                if name == "ask_customer_service":
                    # Run Foundry agent with keep-alive pings to prevent WS timeout
                    agent_task = asyncio.create_task(_call_foundry_agent(question))
                    while not agent_task.done():
                        await asyncio.sleep(2)
                        if not agent_task.done():
                            try:
                                await self.send({"type": "status", "state": "thinking"})
                            except Exception:
                                pass
                    result_text = agent_task.result()
                else:
                    result_text = f"Unknown function: {name}"
                logger.info("[%s] %s returned %d chars", self.client_id, name, len(result_text))
            except Exception as exc:
                logger.error("[%s] Tool error: %s", self.client_id, exc)
                result_text = f"Error: {exc}"

            try:
                from azure.ai.voicelive.models import ConversationRequestItem
                tool_output = ConversationRequestItem(type="function_call_output")
                tool_output["call_id"] = call_id
                tool_output["output"] = result_text
                await connection.conversation.item.create(item=tool_output)
                await connection.response.create()
            except Exception as exc:
                logger.error("[%s] Tool output error: %s", self.client_id, exc)

        # ── Response events ──
        elif event_type == ServerEventType.RESPONSE_CREATED.value:
            pass  # Don't set speaking yet — wait for actual audio/text

        elif event_type == "response.text.delta":
            delta_text = getattr(event, "delta", "")
            if delta_text:
                self._assistant_transcript += delta_text
                await self.send({"type": "status", "state": "speaking"})
                await self.send(
                    {
                        "type": "transcript",
                        "role": "assistant",
                        "text": self._assistant_transcript,
                        "isFinal": False,
                    }
                )

        elif event_type == ServerEventType.RESPONSE_AUDIO_DELTA.value:
            self._is_processing = True  # Mark as processing during audio output too
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
            # Log what the response contains
            response_obj = getattr(event, "response", None)
            if response_obj:
                output = getattr(response_obj, "output", []) or []
                output_types = [getattr(item, "type", "unknown") for item in output]
                logger.info("[%s] Response done. Output types: %s", self.client_id, output_types)
            else:
                logger.info("[%s] Response done. No response object.", self.client_id)

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

            self._is_processing = False
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


@router.post("/tts")
async def text_to_speech(request: Request):
    """Convert text to speech using gpt-realtime-mini (same voice as voice chat)."""
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        return Response(status_code=400, content="No text provided")

    endpoint = settings.azure_voicelive_endpoint or settings.azure_openai_endpoint
    if not endpoint:
        return Response(status_code=503, content="Voice endpoint not configured")

    # Strip markdown before speaking
    clean = clean_text_for_speech(text)
    if not clean:
        return Response(status_code=400, content="No speakable text")

    credential: Any
    if settings.azure_voicelive_api_key:
        credential = AzureKeyCredential(settings.azure_voicelive_api_key)
    else:
        credential = DefaultAzureCredential()

    audio_chunks: list[bytes] = []

    try:
        async with connect(
            endpoint=endpoint,
            credential=credential,
            model=settings.voicelive_model,
        ) as connection:
            voice_name = (settings.voicelive_voice or "alloy").strip()
            voice_val: Any = resolve_voice(voice_name)

            session = RequestSession(
                modalities=[Modality.AUDIO],
                voice=voice_val,
                instructions="Read the following text naturally.",
                output_audio_format=OutputAudioFormat.PCM16,
            )
            await connection.session.update(session=session)

            # Inject text and request response
            await connection.conversation.item.create(
                item={
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": clean}],
                }
            )
            await connection.response.create()

            # Collect audio
            async for event in connection:
                raw_type = getattr(event, "type", None)
                event_type = getattr(raw_type, "value", raw_type)

                if event_type == ServerEventType.RESPONSE_AUDIO_DELTA.value:
                    delta = getattr(event, "delta", None)
                    if delta:
                        if isinstance(delta, bytes):
                            audio_chunks.append(delta)
                        else:
                            audio_chunks.append(base64.b64decode(delta))

                elif event_type == ServerEventType.RESPONSE_DONE.value:
                    break

                elif event_type == ServerEventType.ERROR.value:
                    error_obj = getattr(event, "error", None)
                    msg = getattr(error_obj, "message", str(error_obj or event))
                    logger.error("TTS error: %s", msg)
                    break

    except Exception as exc:
        logger.error("TTS failed: %s", exc)
        return Response(status_code=500, content="TTS error")
    finally:
        close_fn = getattr(credential, "close", None)
        if callable(close_fn):
            result = close_fn()
            if asyncio.iscoroutine(result):
                await result

    if not audio_chunks:
        return Response(status_code=500, content="No audio generated")

    # Return raw PCM16 audio
    pcm_data = b"".join(audio_chunks)
    return Response(
        content=pcm_data,
        media_type="audio/pcm",
        headers={
            "X-Sample-Rate": "24000",
            "X-Channels": "1",
            "X-Format": "pcm16",
        },
    )


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
    endpoint = resolve_endpoint(settings.azure_voicelive_endpoint, settings.azure_openai_endpoint)
    if not endpoint:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "message": "Missing realtime endpoint. Set AZURE_OPENAI_ENDPOINT or AZURE_VOICELIVE_ENDPOINT.",
                }
            )
        )
        return

    if not is_valid_realtime_endpoint(endpoint):
        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "message": "Realtime websocket requires an Azure OpenAI endpoint host (*.openai.azure.com).",
                }
            )
        )
        return

    credential = resolve_credential(settings.azure_voicelive_api_key)

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
