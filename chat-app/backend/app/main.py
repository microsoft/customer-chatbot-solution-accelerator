import json
import logging
import os
import re
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from opentelemetry import trace
except ImportError:

    class _Trace:
        @staticmethod
        def get_current_span():
            return None

    trace = _Trace()

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    configure_azure_monitor = None
    FastAPIInstrumentor = None

_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path, override=False)

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
for logger_name in AZURE_LOGGING_PACKAGES:
    logging.getLogger(logger_name).setLevel(
        getattr(logging, AZURE_PACKAGE_LOGGING_LEVEL, logging.WARNING)
    )
logging.getLogger("agent_framework_azure_ai._client").setLevel(logging.ERROR)
try:
    from .auth import get_current_user
    from .config import settings
    from .routers import auth, chat, chat_config, voice_live
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.auth import get_current_user
    from app.config import settings
    from app.routers import auth, chat, chat_config, voice_live

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI customer support chat API",
    docs_url="/docs",
    redoc_url="/redoc",
)

instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if (
    instrumentation_key
    and configure_azure_monitor is not None
    and FastAPIInstrumentor is not None
):
    configure_azure_monitor(
        connection_string=instrumentation_key,
        enable_live_metrics=False,
        enable_performance_counters=False,
        instrumentation_options={
            "fastapi": {"enabled": False},
        },
    )
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="/health$,/robots933456\\.txt$,/api/auth/me$",
        exclude_spans=["receive", "send"],
    )
    logging.info(
        "Application Insights configured with FastAPI instrumentation"
    )
elif instrumentation_key and (
    configure_azure_monitor is None or FastAPIInstrumentor is None
):
    logging.warning(
        "Application Insights connection string is set but OpenTelemetry "
        "packages are missing; install azure-monitor-opentelemetry to enable "
        "telemetry."
    )
else:
    logging.warning(
        "No Application Insights connection string found. Telemetry disabled."
    )

_SESSION_PATH_RE = re.compile(r"/api/chat/sessions/([^/]+)")


@app.middleware("http")
async def attach_trace_attributes(request: Request, call_next):
    span = trace.get_current_span()
    if span and span.is_recording():
        user_id = request.headers.get("x-ms-client-principal-id") or "guest-user-00000000"
        span.set_attribute("user_id", user_id)

        match = _SESSION_PATH_RE.match(request.url.path)
        if match and match.group(1) != "new":
            span.set_attribute("session_id", match.group(1))
        else:
            sid = request.query_params.get("session_id")
            if sid:
                span.set_attribute("session_id", sid)
            elif request.method == "POST" and "application/json" in (request.headers.get("content-type") or ""):
                try:
                    body = await request.body()
                    if body:
                        data = json.loads(body)
                        sid = data.get("session_id")
                        if sid:
                            span.set_attribute("session_id", sid)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    logger.debug("Failed to parse request body for session_id: %s", exc)

    return await call_next(request)


_cors_origins = frozenset(settings.allowed_origins)


class _FixCredentialedCorsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin")
        if origin and origin in _cors_origins:
            response.headers["access-control-allow-origin"] = origin
            response.headers["access-control-allow-credentials"] = "true"
        return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(_cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(_FixCredentialedCorsMiddleware)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(chat_config.router)
app.include_router(voice_live.router)


@app.get("/")
async def read_root():
    return {
        "message": f"Welcome to {settings.app_name}!",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if settings.cosmos_db_endpoint else "not_configured",
        "openai": "configured" if settings.azure_openai_endpoint else "not_configured",
        "auth": "configured" if settings.azure_client_id else "not_configured",
        "version": "minimal",
    }


@app.get("/debug/auth")
async def debug_auth(request: Request):
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
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
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
