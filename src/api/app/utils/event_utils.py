import logging
import os

from opentelemetry import trace

logger = logging.getLogger(__name__)

_app_insights_configured = bool(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))


def track_event_if_configured(event_name: str, properties: dict = None):
    """Track a custom event to Application Insights via OpenTelemetry span events.

    Only emits events when Application Insights is configured. Uses the current
    active span to attach the event, so it inherits operation_id / parent context.
    """
    if not _app_insights_configured:
        return

    span = trace.get_current_span()
    if span and span.is_recording():
        attributes = {k: str(v) for k, v in (properties or {}).items() if v is not None}
        span.add_event(event_name, attributes=attributes)
