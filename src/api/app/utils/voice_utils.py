"""
Voice utility functions — credential resolution, voice config helpers, text cleaning.
"""
import re
from typing import Any

from azure.ai.voicelive.models import AzureStandardVoice
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential


# OpenAI realtime voice names (passed as plain strings, not AzureStandardVoice)
REALTIME_VOICES = frozenset({
    "alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse",
})


def resolve_voice(voice_name: str) -> Any:
    """Resolve a voice name to the correct SDK type."""
    voice_name = (voice_name or "").strip()
    if not voice_name:
        return None
    if voice_name.lower() in REALTIME_VOICES:
        return voice_name
    return AzureStandardVoice(name=voice_name)


def resolve_credential(api_key: str | None) -> Any:
    """Return AzureKeyCredential if key provided, else DefaultAzureCredential."""
    if api_key:
        return AzureKeyCredential(api_key)
    return DefaultAzureCredential()


def resolve_endpoint(voicelive_endpoint: str | None, openai_endpoint: str | None) -> str | None:
    """Pick the correct Azure OpenAI endpoint for realtime connections."""
    endpoint = voicelive_endpoint or openai_endpoint
    if not endpoint:
        return None
    host = endpoint.lower()
    # Prefer openai.azure.com host over services.ai.azure.com
    if "services.ai.azure.com" in host and openai_endpoint:
        endpoint = openai_endpoint
    return endpoint


def is_valid_realtime_endpoint(endpoint: str) -> bool:
    """Check if endpoint is a valid Azure OpenAI host for realtime."""
    return "openai.azure.com" in endpoint.lower()


# Markdown/URL patterns for TTS text cleaning
_CLEAN_PATTERNS: list[tuple[str, str]] = [
    (r'\[([^\]]+)\]\([^)]+\)', r'\1'),
    (r'https?://[^\s)]+', ''),
    (r'\*\*([^*]+)\*\*', r'\1'),
    (r'\*([^*]+)\*', r'\1'),
    (r'#{1,6}\s*', ''),
    (r'```[\s\S]*?```', ''),
    (r'`([^`]+)`', r'\1'),
    (r'\n{2,}', '. '),
    (r'\s{2,}', ' '),
]


def clean_text_for_speech(text: str) -> str:
    """Strip markdown, URLs, and code from text for natural TTS."""
    result = text
    for pattern, replacement in _CLEAN_PATTERNS:
        result = re.sub(pattern, replacement, result)
    return result.strip()
