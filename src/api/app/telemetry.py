"""Process-wide telemetry singletons.

A single :class:`TokenUsageEmitter` is constructed at import time so every
router/utility shares the same App Insights connection-string resolution and
static dimensions. Importing this module has no side effects beyond reading
``APPLICATIONINSIGHTS_CONNECTION_STRING`` from the environment.
"""
from __future__ import annotations

try:
    from .utils.llm_token_telemetry import TokenUsageEmitter
except ImportError:
    from app.utils.llm_token_telemetry import TokenUsageEmitter

token_emitter = TokenUsageEmitter(
    static_dimensions={"app": "customer-chatbot"},
)

__all__ = ["token_emitter"]
