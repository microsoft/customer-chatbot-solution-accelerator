from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import sys
import os

# Handle both local debugging and Docker deployment
try:
    # Try relative imports first (for Docker)
    from .config import settings
    from .routers import products, chat, cart, auth
    from .auth import get_current_user
except ImportError:
    # Fall back to absolute imports (for local debugging)
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.config import settings
    from app.routers import products, chat, cart, auth
    from app.auth import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="E-commerce Chat API with AI-powered customer support",
    docs_url="/docs",
    redoc_url="/redoc"
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
app.include_router(chat.router)
app.include_router(cart.router)

@app.get("/")
async def read_root():
    """Root endpoint with API information"""
    return {
        "message": f"Welcome to {settings.app_name}!",
        "version": settings.app_version,
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if settings.cosmos_db_endpoint else "mock",
        "openai": "configured" if settings.azure_openai_endpoint else "not_configured",
        "auth": "configured" if settings.azure_client_id else "not_configured",
        "version": "minimal"
    }

@app.get("/debug/auth")
async def debug_auth(request: Request):
    """Debug endpoint to see authentication headers and current user info"""
    try:
        headers = dict(request.headers)
        current_user = await get_current_user(request)
        
        return {
            "headers": {k: v for k, v in headers.items() if 'x-ms-' in k.lower() or 'authorization' in k.lower()},
            "all_headers_count": len(headers),
            "current_user": current_user,
            "debug_info": {
                "has_principal_id": 'x-ms-client-principal-id' in headers,
                "has_principal": 'x-ms-client-principal' in headers,
                "has_principal_name": 'x-ms-client-principal-name' in headers,
                "is_guest": current_user.get("is_guest", "unknown")
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "headers": dict(request.headers)
        }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error": exc.detail
        }
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
            "error": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )