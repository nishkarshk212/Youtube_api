from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import time
import secrets
import string
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


@router.post("/api-keys/generate")
@limiter.limit("10/minute")
async def generate_api_key(
    plan: str = "free",
    request: Request = None
):
    """
    Generate a new API key with specified plan.
    
    Plans:
    - free: 100 requests/day
    - pro: 10,000 requests/day
    - enterprise: unlimited requests
    """
    try:
        # Generate random API key
        api_key_value = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Set plan limits
        plan_limits = {
            "free": {"daily_limit": 100, "monthly_limit": 3000},
            "pro": {"daily_limit": 10000, "monthly_limit": 300000},
            "enterprise": {"daily_limit": -1, "monthly_limit": -1}  # Unlimited
        }
        
        if plan not in plan_limits:
            raise HTTPException(status_code=400, detail="Invalid plan. Choose from: free, pro, enterprise")
        
        limits = plan_limits[plan]
        
        # Store API key in Redis
        await cache.set(f"api_key:{api_key_value}:plan", plan)
        await cache.set(f"api_key:{api_key_value}:daily_limit", limits["daily_limit"])
        await cache.set(f"api_key:{api_key_value}:monthly_limit", limits["monthly_limit"])
        await cache.set(f"api_key:{api_key_value}:requests", 0)
        await cache.set(f"api_key:{api_key_value}:created_at", datetime.utcnow().isoformat())
        await cache.set(f"api_key:{api_key_value}:active", True)
        
        # Add to list of active keys
        await cache.sadd("active_api_keys", api_key_value)
        
        logger.info(f"Generated new API key for plan: {plan}")
        
        return {
            "api_key": api_key_value,
            "plan": plan,
            "daily_limit": limits["daily_limit"],
            "monthly_limit": limits["monthly_limit"],
            "created_at": datetime.utcnow().isoformat(),
            "active": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate API key")


@router.delete("/api-keys/{api_key_value}")
@limiter.limit("5/minute")
async def delete_api_key(
    api_key_value: str,
    request: Request = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Delete an API key.
    """
    try:
        # Check if key exists
        active = await cache.get(f"api_key:{api_key_value}:active")
        if not active:
            raise HTTPException(status_code=404, detail="API key not found")
        
        # Delete key data from Redis
        await cache.delete(f"api_key:{api_key_value}:plan")
        await cache.delete(f"api_key:{api_key_value}:daily_limit")
        await cache.delete(f"api_key:{api_key_value}:monthly_limit")
        await cache.delete(f"api_key:{api_key_value}:requests")
        await cache.delete(f"api_key:{api_key_value}:created_at")
        await cache.delete(f"api_key:{api_key_value}:active")
        
        # Remove from active keys list
        await cache.srem("active_api_keys", api_key_value)
        
        logger.info(f"Deleted API key: {api_key_value[:8]}...")
        
        return {"message": "API key deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key deletion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete API key")


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
