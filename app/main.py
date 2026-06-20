import ssl
import urllib3
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from datetime import datetime
from loguru import logger
import time

# Disable SSL verification globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

from app.config import settings
from app.cache import cache
from app.extractor import extractor
from app.auth import verify_api_key, get_optional_api_key
from app.routers import search, video, audio, playlist, trending, health, admin

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Startup time
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    logger.info("Starting YouTube Music API...")
    await cache.connect()
    logger.info("API started successfully")
    yield
    # Shutdown
    logger.info("Shutting down YouTube Music API...")
    await cache.disconnect()
    logger.info("API shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="YouTube Music API",
    description="Production-ready YouTube Music API for Telegram music bots",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None
        }
    )


# Include routers
app.include_router(search.router, prefix="/api", tags=["Search"])
app.include_router(video.router, prefix="/api", tags=["Video"])
app.include_router(audio.router, prefix="/api", tags=["Audio"])
app.include_router(playlist.router, prefix="/api", tags=["Playlist"])
app.include_router(trending.router, prefix="/api", tags=["Trending"])
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"], dependencies=[Depends(verify_api_key)])


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "YouTube Music API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=int(settings.API_PORT),
        reload=settings.ENVIRONMENT == "development"
    )
