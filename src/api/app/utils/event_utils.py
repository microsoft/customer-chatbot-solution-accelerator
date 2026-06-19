import importlib
import logging
import os

try:
    track_event = importlib.import_module("azure.monitor.events.extension").track_event
except (ImportError, AttributeError):
    track_event = None

logger = logging.getLogger(__name__)


def track_event_if_configured(event_name: str, properties: dict | None = None):
    """Track a custom event to Application Insights via azure-monitor-events-extension.

    Uses track_event from azure.monitor.events.extension which writes to the
    customEvents table in Application Insights (not traces).
    Only emits events when Application Insights is configured.
    """
    instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if instrumentation_key and track_event is not None:
        track_event(event_name, properties or {})
    elif instrumentation_key and track_event is None:
        logger.warning(
            "Skipping track_event for %s because azure-monitor-events-extension is unavailable",
            event_name,
        )
    else:
        logger.warning(
            "Skipping track_event for %s as Application Insights is not configured",
            event_name,
        )
