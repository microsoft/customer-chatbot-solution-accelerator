"""
Tests for app.utils.voice_utils — voice utility functions.
"""
from unittest.mock import MagicMock

import pytest
from app.utils.voice_utils import (
    clean_text_for_speech,
    is_valid_realtime_endpoint,
    resolve_credential,
    resolve_endpoint,
    resolve_voice,
)
from azure.ai.voicelive.models import AzureStandardVoice
from azure.core.credentials import AzureKeyCredential
from azure.identity.aio import DefaultAzureCredential as AioDefaultAzureCredential
from azure.identity.aio import ManagedIdentityCredential as AioManagedIdentityCredential

# =============================================================================
# resolve_voice
# =============================================================================


def test_resolve_voice_realtime():
    """Realtime voice names (alloy, echo, etc.) are returned as plain strings."""
    assert resolve_voice("alloy") == "alloy"
    assert resolve_voice("echo") == "echo"
    assert resolve_voice("shimmer") == "shimmer"


def test_resolve_voice_case_insensitive():
    """Voice name lookup is case-insensitive."""
    assert resolve_voice("Alloy") == "Alloy"
    assert resolve_voice("ECHO") == "ECHO"


def test_resolve_voice_azure_standard():
    """Non-realtime voice names return AzureStandardVoice."""
    result = resolve_voice("en-US-Ava:DragonHDLatestNeural")
    assert isinstance(result, AzureStandardVoice)
    assert result.name == "en-US-Ava:DragonHDLatestNeural"


def test_resolve_voice_empty():
    """Empty voice name returns None."""
    assert resolve_voice("") is None
    assert resolve_voice("   ") is None


# =============================================================================
# resolve_credential
# =============================================================================


@pytest.mark.asyncio
async def test_resolve_credential_with_key():
    """API key returns AzureKeyCredential."""
    cred = await resolve_credential("my-api-key")
    assert isinstance(cred, AzureKeyCredential)


@pytest.mark.asyncio
async def test_resolve_credential_without_key(monkeypatch):
    """No API key returns env-aware credential (DefaultAzureCredential in dev)."""
    monkeypatch.setenv("APP_ENV", "dev")
    cred = await resolve_credential(None)
    assert isinstance(cred, AioDefaultAzureCredential)


@pytest.mark.asyncio
async def test_resolve_credential_empty_string(monkeypatch):
    """Empty string returns env-aware credential (DefaultAzureCredential in dev)."""
    monkeypatch.setenv("APP_ENV", "dev")
    cred = await resolve_credential("")
    assert isinstance(cred, AioDefaultAzureCredential)


@pytest.mark.asyncio
async def test_resolve_credential_prod(monkeypatch):
    """In prod returns ManagedIdentityCredential."""
    monkeypatch.setenv("APP_ENV", "prod")
    cred = await resolve_credential(None)
    assert isinstance(cred, AioManagedIdentityCredential)


# =============================================================================
# resolve_endpoint
# =============================================================================


def test_resolve_endpoint_voicelive():
    """Returns voicelive endpoint when set."""
    assert resolve_endpoint("https://voice.openai.azure.com", None) == "https://voice.openai.azure.com"


def test_resolve_endpoint_openai_fallback():
    """Falls back to openai endpoint when voicelive is None."""
    assert resolve_endpoint(None, "https://openai.azure.com") == "https://openai.azure.com"


def test_resolve_endpoint_none():
    """Returns None when both are None."""
    assert resolve_endpoint(None, None) is None


def test_resolve_endpoint_prefers_openai_over_services():
    """When voicelive host is services.ai.azure.com, prefer openai_endpoint."""
    result = resolve_endpoint(
        "https://myproject.services.ai.azure.com",
        "https://myopenai.openai.azure.com",
    )
    assert result == "https://myopenai.openai.azure.com"


def test_resolve_endpoint_services_no_openai_fallback():
    """When voicelive is services.ai.azure.com and no openai, keep it."""
    result = resolve_endpoint("https://myproject.services.ai.azure.com", None)
    assert result == "https://myproject.services.ai.azure.com"


# =============================================================================
# is_valid_realtime_endpoint
# =============================================================================


def test_is_valid_realtime_endpoint_valid():
    assert is_valid_realtime_endpoint("https://myhost.openai.azure.com") is True


def test_is_valid_realtime_endpoint_invalid():
    assert is_valid_realtime_endpoint("https://myhost.services.ai.azure.com") is False


def test_is_valid_realtime_endpoint_case_insensitive():
    assert is_valid_realtime_endpoint("https://HOST.OpenAI.Azure.COM") is True


# =============================================================================
# clean_text_for_speech
# =============================================================================


def test_clean_text_strips_urls():
    result = clean_text_for_speech("Visit https://example.com for info")
    assert "https://" not in result
    assert "Visit" in result and "for info" in result


def test_clean_text_strips_markdown_links():
    assert clean_text_for_speech("[click here](https://example.com)") == "click here"


def test_clean_text_strips_bold():
    assert clean_text_for_speech("This is **bold** text") == "This is bold text"


def test_clean_text_strips_italic():
    assert clean_text_for_speech("This is *italic* text") == "This is italic text"


def test_clean_text_strips_headers():
    assert clean_text_for_speech("## Section Title") == "Section Title"


def test_clean_text_strips_code_blocks():
    result = clean_text_for_speech("Before ```code here``` after")
    assert "code here" not in result
    assert "Before" in result


def test_clean_text_strips_inline_code():
    assert clean_text_for_speech("Use `print()` function") == "Use print() function"


def test_clean_text_collapses_whitespace():
    result = clean_text_for_speech("Hello   world")
    assert result == "Hello world"


def test_clean_text_empty_input():
    assert clean_text_for_speech("") == ""


def test_clean_text_only_url():
    result = clean_text_for_speech("https://example.com")
    assert result == ""
