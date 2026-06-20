from fastapi import APIRouter, HTTPException, Query, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from loguru import logger

from app.extractor import extractor
from app.cache import cache
from app.auth import verify_api_key, get_optional_api_key
from app.models import VideoInfo, RelatedResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/video", response_model=VideoInfo)
@limiter.limit("100/minute")
async def get_video(
    request: Request,
    id: str = Query(..., description="YouTube video ID"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Get detailed video information.
    
    Returns comprehensive metadata including title, duration, thumbnail, 
    uploader, view count, upload date, description, tags, and categories.
    """
    try:
        # Check cache
        cache_key = f"video:{id}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for video: {id}")
            return cached

        # Get video info
        info = await extractor.get_video_info(id)
        
        if not info:
            raise HTTPException(status_code=404, detail="Video not found")

        # Cache result
        await cache.set(cache_key, info)
        
        # Increment stats
        await cache.increment("stats:video_requests")
        await cache.increment("stats:successful_requests")

        return info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video info error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Failed to get video information")


@router.get("/related", response_model=RelatedResponse)
@limiter.limit("100/minute")
async def get_related_videos(
    request: Request,
    id: str = Query(..., description="YouTube video ID"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Get related videos for a given video.
    
    Returns a list of related videos with metadata.
    """
    try:
        # Check cache
        cache_key = f"related:{id}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for related: {id}")
            return cached

        # Get related videos
        related = await extractor.get_related(id)
        
        if not related:
            raise HTTPException(status_code=404, detail="No related videos found")

        result = {
            "video_id": id,
            "related": related
        }
        
        # Cache result
        await cache.set(cache_key, result)
        
        # Increment stats
        await cache.increment("stats:related_requests")
        await cache.increment("stats:successful_requests")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Related videos error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Failed to get related videos")
