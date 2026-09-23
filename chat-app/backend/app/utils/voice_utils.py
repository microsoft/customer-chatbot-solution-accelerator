"""
Voice utility functions — credential resolution, voice config helpers, text cleaning.
"""
import re
from typing import Any
from urllib.parse import urlparse

from azure.ai.voicelive.models import AzureStandardVoice
from azure.core.credentials import AzureKeyCredential

from .azure_credential_utils import get_azure_credential_async

# Azure OpenAI realtime voice names (passed as plain strings, not AzureStandardVoice)
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


async def resolve_credential(api_key: str | None, client_id: str | None = None) -> Any:
    """Return AzureKeyCredential if key provided, else env-aware async credential."""
    if api_key:
        return AzureKeyCredential(api_key)
    return await get_azure_credential_async(client_id=client_id)


def _hostname_matches(endpoint: str, suffix: str) -> bool:
    """Return True only if the URL's hostname equals or is a subdomain of `suffix`.

    Guards against incomplete URL substring sanitization (CodeQL
    py/incomplete-url-substring-sanitization): a plain `in` check would match
    attacker-controlled hosts like `openai.azure.com.evil.com` or paths that
    embed the expected domain.
    """
    try:
        hostname = urlparse(endpoint).hostname
    except ValueError:
        return False
    if not hostname:
        return False
    hostname = hostname.lower()
    suffix = suffix.lower()
    return hostname == suffix or hostname.endswith("." + suffix)


def resolve_endpoint(voicelive_endpoint: str | None, openai_endpoint: str | None) -> str | None:
    """Pick the correct Azure OpenAI endpoint for realtime connections."""
    endpoint = voicelive_endpoint or openai_endpoint
    if not endpoint:
        return None
    # Prefer openai.azure.com host over services.ai.azure.com
    if _hostname_matches(endpoint, "services.ai.azure.com") and openai_endpoint:
        endpoint = openai_endpoint
    return endpoint


def is_valid_realtime_endpoint(endpoint: str) -> bool:
    """Check if endpoint is a valid Azure OpenAI host for realtime."""
    return _hostname_matches(endpoint, "openai.azure.com")


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
