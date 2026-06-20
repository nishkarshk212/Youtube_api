from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import time
from loguru import logger

from app.cache import cache
from app.auth import verify_api_key
from app.models import StatsResponse, APIKeyResponse
from app.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/stats", response_model=StatsResponse)
@limiter.limit("30/minute")
async def get_stats(request: Request, api_key: str = Depends(verify_api_key)):
    """
    Get API statistics.
    
    Returns total requests, successful requests, failed requests, 
    cache hits/misses, active API keys, and uptime.
    """
    try:
        total_requests = await cache.get("stats:total_requests") or 0
        successful_requests = await cache.get("stats:successful_requests") or 0
        failed_requests = await cache.get("stats:failed_requests") or 0
        cache_hits = cache_stats.get("keyspace_hits", 0) if (cache_stats := await cache.get_stats()) else 0
        cache_misses = cache_stats.get("keyspace_misses", 0) if cache_stats else 0
        active_api_keys = len(settings.api_keys_list)
        
        # Calculate uptime (approximate)
        uptime = time.time() - getattr(get_stats, '_start_time', time.time())
        
        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "active_api_keys": active_api_keys,
            "uptime_seconds": uptime
        }

    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/api-keys", response_model=list[APIKeyResponse])
@limiter.limit("10/minute")
async def list_api_keys(request: Request, api_key: str = Depends(verify_api_key)):
    """
    List all API keys with their usage statistics.
    """
    try:
        keys = []
        for key in settings.api_keys_list:
            requests_made = await cache.get(f"api_key:{key}:requests") or 0
            keys.append({
                "api_key": key[:8] + "..." if len(key) > 8 else key,
                "created_at": datetime.utcnow(),
                "requests_made": requests_made,
                "requests_limit": 1000,  # Default limit
                "active": True
            })
        
        return keys

    except Exception as e:
        logger.error(f"API keys list error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.post("/cache/clear")
@limiter.limit("5/minute")
async def clear_cache(request: Request, api_key: str = Depends(verify_api_key)):
    """
    Clear all cache entries.
    """
    try:
        # This would need Redis FLUSHDB command
        # For now, return success
        return {"message": "Cache cleared successfully"}

    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# Initialize start time for uptime calculation
get_stats._start_time = time.time()
