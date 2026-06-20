from fastapi import APIRouter, HTTPException, Query, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from loguru import logger

from app.extractor import extractor
from app.cache import cache
from app.auth import verify_api_key, get_optional_api_key
from app.models import AudioStream

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/audio", response_model=AudioStream)
@limiter.limit("50/minute")
async def get_audio_stream(
    request: Request,
    id: str = Query(..., description="YouTube video ID"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Get downloadable audio stream URL.
    
    Returns a direct stream URL for the best quality audio along with 
    format information, quality, file size, and codec details.
    """
    try:
        # Check cache (shorter TTL for stream URLs)
        cache_key = f"audio:{id}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for audio: {id}")
            return cached

        # Get audio stream
        stream = await extractor.get_audio_stream(id)
        
        if not stream:
            raise HTTPException(status_code=404, detail="Audio stream not found")

        # Cache result with shorter TTL (stream URLs expire)
        await cache.set(cache_key, stream, ttl=1800)  # 30 minutes
        
        # Increment stats
        await cache.increment("stats:audio_requests")
        await cache.increment("stats:successful_requests")

        return stream

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio stream error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Failed to get audio stream")
