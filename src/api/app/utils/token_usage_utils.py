"""Deprecated shim — use :mod:`app.utils.llm_token_telemetry` instead.

This module preserves the public symbols of the previous bespoke
``token_usage_utils`` for backward compatibility with any out-of-tree
importers. All implementations now delegate to ``llm_token_telemetry``.

Removed in a future release.
"""
from __future__ import annotations

import warnings
from typing import Any, Dict, Optional, Tuple

from .llm_token_telemetry import (
    TokenUsage,
    TokenUsageEmitter,
    extract_realtime_usage as _extract_realtime_usage,
    extract_usage as _extract_usage,
)

warnings.warn(
    "app.utils.token_usage_utils is deprecated; "
    "use app.utils.llm_token_telemetry instead.",
    DeprecationWarning,
    stacklevel=2,
)

_default_emitter = TokenUsageEmitter()


def extract_usage_from_agent_result(result: Any) -> Optional[Tuple[int, int, int]]:
    """Legacy tuple-returning extractor. Prefer :func:`extract_usage`."""
    u = _extract_usage(result)
    if u is None:
        return None
    return u.input_tokens, u.output_tokens, u.total_tokens


def extract_realtime_usage(response_obj: Any) -> Optional[Dict[str, int]]:
    """Legacy dict-returning realtime extractor."""
    u = _extract_realtime_usage(response_obj)
    if u is None:
        return None
    return {
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "total_tokens": u.total_tokens,
        "input_audio_tokens": u.input_audio_tokens or 0,
        "input_text_tokens": u.input_text_tokens or 0,
        "input_cached_tokens": u.input_cached_tokens or 0,
        "output_audio_tokens": u.output_audio_tokens or 0,
        "output_text_tokens": u.output_text_tokens or 0,
    }


def track_token_usage(
    *,
    agent_name: str,
    model_deployment_name: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    additional_agents: Optional[Dict[str, str]] = None,
) -> None:
    """Legacy emitter wrapper. Prefer :class:`TokenUsageEmitter`."""
    usage = TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens or (input_tokens + output_tokens),
    )
    _default_emitter.emit_all(
        agent_name=agent_name,
        model_deployment_name=model_deployment_name,
        usage=usage,
        additional_agents=additional_agents,
        user_id=user_id,
        session_id=session_id,
    )


def extract_and_track_usage(
    result: Any,
    *,
    agent_name: str,
    model_deployment_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    additional_agents: Optional[Dict[str, str]] = None,
) -> Optional[Tuple[int, int, int]]:
    """Legacy convenience wrapper combining extraction and emission."""
    u = _extract_usage(result)
    if u is None:
        return None
    _default_emitter.emit_all(
        agent_name=agent_name,
        model_deployment_name=model_deployment_name,
        usage=u,
        additional_agents=additional_agents,
        user_id=user_id,
        session_id=session_id,
    )
    return u.input_tokens, u.output_tokens, u.total_tokens


def track_speech_usage(
    *,
    model_deployment_name: str,
    source: str,
    counts: Dict[str, int],
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Legacy speech emitter."""
    usage = TokenUsage(
        input_tokens=int(counts.get("input_tokens", 0)),
        output_tokens=int(counts.get("output_tokens", 0)),
        total_tokens=int(counts.get("total_tokens", 0)),
        input_audio_tokens=int(counts.get("input_audio_tokens", 0)),
        input_text_tokens=int(counts.get("input_text_tokens", 0)),
        input_cached_tokens=int(counts.get("input_cached_tokens", 0)),
        output_audio_tokens=int(counts.get("output_audio_tokens", 0)),
        output_text_tokens=int(counts.get("output_text_tokens", 0)),
    )
    _default_emitter.emit_speech(
        model_deployment_name=model_deployment_name,
        source=source,
        usage=usage,
        user_id=user_id,
        session_id=session_id,
    )


def extract_and_track_speech_usage(
    response_obj: Any,
    *,
    model_deployment_name: str,
    source: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Optional[Dict[str, int]]:
    """Legacy convenience wrapper for Voice Live usage."""
    u = _extract_realtime_usage(response_obj)
    if u is None:
        return None
    _default_emitter.emit_speech(
        model_deployment_name=model_deployment_name,
        source=source,
        usage=u,
        user_id=user_id,
        session_id=session_id,
    )
    return extract_realtime_usage(response_obj)


__all__ = [
    "extract_usage_from_agent_result",
    "extract_realtime_usage",
    "track_token_usage",
    "extract_and_track_usage",
    "track_speech_usage",
    "extract_and_track_speech_usage",
]
