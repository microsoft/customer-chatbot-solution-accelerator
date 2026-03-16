import logging
import os
import re
import sys

import uvicorn
from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure logging BEFORE importing other modules
# This ensures all loggers created in imported modules inherit this configuration
# Configurable via environment variables (matching Conversation-Knowledge-Mining pattern)
AZURE_BASIC_LOGGING_LEVEL = os.getenv("AZURE_BASIC_LOGGING_LEVEL", "INFO").upper()
AZURE_PACKAGE_LOGGING_LEVEL = os.getenv("AZURE_PACKAGE_LOGGING_LEVEL", "WARNING").upper()
AZURE_LOGGING_PACKAGES = [
    pkg.strip()
    for pkg in os.getenv("AZURE_LOGGING_PACKAGES", "").split(",")
    if pkg.strip()
]

logging.basicConfig(
    level=getattr(logging, AZURE_BASIC_LOGGING_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)

# Suppress noisy Azure SDK / third-party loggers at the configured package level
_default_suppressed_loggers = [
    "azure.core.pipeline.policies.http_logging_policy",
    "azure.core.pipeline.policies._universal",
    "azure.identity",
    "azure.monitor.opentelemetry.exporter.export._base",
    "azure.cosmos",
    "httpx",
    "httpcore",
    "app.utils.auth_utils",
    "app.routers.auth",
    "app.auth",
]
for logger_name in _default_suppressed_loggers:
    logging.getLogger(logger_name).setLevel(
        getattr(logging, AZURE_PACKAGE_LOGGING_LEVEL, logging.WARNING)
    )
# Additional packages from env var
for logger_name in AZURE_LOGGING_PACKAGES:
    logging.getLogger(logger_name).setLevel(
        getattr(logging, AZURE_PACKAGE_LOGGING_LEVEL, logging.WARNING)
    )
# Always suppress agent framework at ERROR level
logging.getLogger("agent_framework_azure_ai._client").setLevel(logging.ERROR)
# Handle both local debugging and Docker deployment
try:
    # Try relative imports first (for Docker)
    from .auth import get_current_user
    from .config import settings
    from .routers import auth, cart, chat, products
except ImportError:
    # Fall back to absolute imports (for local debugging)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.auth import get_current_user
    from app.config import settings
    from app.routers import auth, cart, chat, products

# Get logger for this module (logging already configured above)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="E-commerce Chat API with AI-powered customer support",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Azure Monitor and instrument FastAPI for OpenTelemetry
# This enables automatic request tracing, dependency tracking, and proper operation_id
instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if instrumentation_key:
    configure_azure_monitor(
        connection_string=instrumentation_key,
        enable_live_metrics=True
    )
    # Exclude noisy health probe endpoint from telemetry
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="/health$,/robots933456\\.txt$",
    )
    logging.info(
        "Application Insights configured with live metrics and FastAPI instrumentation"
    )
else:
    logging.warning(
        "No Application Insights connection string found. Telemetry disabled."
    )

# Regex for extracting session_id from URL paths like /api/chat/sessions/{session_id}
_SESSION_PATH_RE = re.compile(r"/api/chat/sessions/([^/]+)")


@app.middleware("http")
async def attach_trace_attributes(request: Request, call_next):
    """Auto-attach session_id and user_id to the current OpenTelemetry span."""
    span = trace.get_current_span()
    if span and span.is_recording():
        # user_id from Easy Auth header
        user_id = request.headers.get("x-ms-client-principal-id")
        if user_id:
            span.set_attribute("user_id", user_id)

        # session_id from path: /api/chat/sessions/{session_id}
        match = _SESSION_PATH_RE.match(request.url.path)
        if match and match.group(1) != "new":
            span.set_attribute("session_id", match.group(1))
        else:
            # Fall back to query parameter (e.g., /api/chat/history?session_id=...)
            sid = request.query_params.get("session_id")
            if sid:
                span.set_attribute("session_id", sid)

    return await call_next(request)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(chat.router)
app.include_router(cart.router)


@app.get("/")
async def read_root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}!",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if settings.cosmos_db_endpoint else "not_configured",
        "openai": "configured" if settings.azure_openai_endpoint else "not_configured",
        "auth": "configured" if settings.azure_client_id else "not_configured",
        "version": "minimal",
    }


@app.get("/debug/auth")
async def debug_auth(request: Request):
    """Debug endpoint to see authentication headers and current user info"""
    try:
        headers = dict(request.headers)
        current_user = await get_current_user(request)

        return {
            "headers": {
                k: v
                for k, v in headers.items()
                if "x-ms-" in k.lower() or "authorization" in k.lower()
            },
            "all_headers_count": len(headers),
            "current_user": current_user,
            "debug_info": {
                "has_principal_id": "x-ms-client-principal-id" in headers,
                "has_principal": "x-ms-client-principal" in headers,
                "has_principal_name": "x-ms-client-principal-name" in headers,
                "is_guest": current_user.get("is_guest", "unknown"),
            },
        }
    except Exception as e:
        return {"error": str(e), "headers": dict(request.headers)}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", host=settings.host, port=settings.port, reload=settings.debug
    )
