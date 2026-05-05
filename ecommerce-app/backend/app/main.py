import logging
import os
import sys

import uvicorn
from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging BEFORE importing other modules
# This ensures all loggers created in imported modules inherit this configuration
logging.basicConfig(
    level=logging.INFO,
    force=True,  # Force reconfiguration even if logging was already configured
)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("app.routers.auth").setLevel(logging.WARNING)
logging.getLogger("app.auth").setLevel(logging.WARNING)

# Handle both local debugging and Docker deployment
try:
    # Try relative imports first (for Docker)
    from .auth import get_current_user
    from .config import settings
    from .routers import auth, cart, products, orders
except ImportError:
    # Fall back to absolute imports (for local debugging)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.auth import get_current_user
    from app.config import settings
    from app.routers import auth, cart, products, orders

# Get logger for this module (logging already configured above)
logger = logging.getLogger(__name__)

# Check if the Application Insights Instrumentation Key is set in the environment variables
instrumentation_key = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if instrumentation_key:
    # Configure Application Insights if the Instrumentation Key is found
    configure_azure_monitor(connection_string=instrumentation_key)
    logging.info("Application Insights configured with the provided Instrumentation Key")
else:
    # Log a warning if the Instrumentation Key is not found
    logging.warning("No Application Insights Instrumentation Key found. Skipping configuration")

# Create FastAPI app
app = FastAPI(
    title="E-commerce API",
    version="1.0.0",
    description="E-commerce platform with product browsing, cart management, and order processing",
    docs_url="/docs",
    redoc_url="/redoc",
)

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
app.include_router(cart.router)
app.include_router(orders.router)


@app.get("/")
async def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to E-commerce API!",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy",
        "service": "ecommerce"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ecommerce",
        "database": "connected" if settings.cosmos_db_endpoint else "not_configured",
        "search": "configured" if settings.azure_search_endpoint else "not_configured",
        "auth": "configured" if settings.azure_client_id else "not_configured",
        "version": "1.0.0",
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler"""
    logger.error(f"HTTP {exc.status_code} error at {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "service": "ecommerce"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors"""
    logger.exception(f"Unexpected error at {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "service": "ecommerce"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)