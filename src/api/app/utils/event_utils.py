import logging
import os

from azure.monitor.events.extension import track_event

logger = logging.getLogger(__name__)


def track_event_if_configured(event_name: str, properties: dict | None = None):
    """Track a custom event to Application Insights via azure-monitor-events-extension.

    Uses track_event from azure.monitor.events.extension which writes to the
    customEvents table in Application Insights (not traces).
    Only emits events when Application Insights is configured.
    """
    instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if instrumentation_key:
        track_event(event_name, properties or {})
    else:
        logger.warning(
            "Skipping track_event for %s as Application Insights is not configured",
            event_name,
        )
