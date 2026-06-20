from fastapi import APIRouter
from datetime import datetime
import time

from app.cache import cache
from app.extractor import extractor
from app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns API status, timestamp, version, cache status, and extractor version.
    """
    cache_stats = await cache.get_stats()
    extractor_version = await extractor.get_extractor_version()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "cache_status": "connected" if cache_stats.get("enabled") else "disabled",
        "extractor_version": extractor_version
    }
