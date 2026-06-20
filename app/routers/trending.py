from fastapi import APIRouter, HTTPException, Query, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from loguru import logger

from app.extractor import extractor
from app.cache import cache
from app.auth import verify_api_key, get_optional_api_key
from app.models import TrendingResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/trending", response_model=TrendingResponse)
@limiter.limit("30/minute")
async def get_trending(
    request: Request,
    category: str = Query("music", description="Category (music, gaming, news, etc.)"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Get trending videos.
    
    Returns a list of trending videos in the specified category with metadata.
    """
    try:
        # Check cache
        cache_key = f"trending:{category}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for trending: {category}")
            return cached

        # Get trending videos
        trending = await extractor.get_trending(category)
        
        if not trending:
            raise HTTPException(status_code=404, detail="No trending videos found")

        result = {
            "category": category,
            "results": trending
        }
        
        # Cache result with shorter TTL (trending changes frequently)
        await cache.set(cache_key, result, ttl=1800)  # 30 minutes
        
        # Increment stats
        await cache.increment("stats:trending_requests")
        await cache.increment("stats:successful_requests")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trending error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Failed to get trending videos")
