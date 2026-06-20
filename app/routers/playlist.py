from fastapi import APIRouter, HTTPException, Query, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from loguru import logger

from app.extractor import extractor
from app.cache import cache
from app.auth import verify_api_key, get_optional_api_key
from app.models import PlaylistInfo

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/playlist", response_model=PlaylistInfo)
@limiter.limit("50/minute")
async def get_playlist(
    request: Request,
    id: str = Query(..., description="YouTube playlist ID"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Get playlist information and tracks.
    
    Returns playlist metadata along with all tracks including title, 
    duration, thumbnail, uploader, and video ID for each track.
    """
    try:
        # Check cache
        cache_key = f"playlist:{id}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for playlist: {id}")
            return cached

        # Get playlist info
        playlist = await extractor.get_playlist(id)
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")

        # Cache result
        await cache.set(cache_key, playlist)
        
        # Increment stats
        await cache.increment("stats:playlist_requests")
        await cache.increment("stats:successful_requests")

        return playlist

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Playlist error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Failed to get playlist information")
