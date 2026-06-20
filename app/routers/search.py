from fastapi import APIRouter, HTTPException, Query, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from loguru import logger
import secrets
import string
from datetime import datetime

from app.extractor import extractor
from app.cache import cache
from app.auth import verify_api_key, get_optional_api_key
from app.models import SearchResult, LyricsResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/search", response_model=list[SearchResult])
@limiter.limit("100/minute")
async def search_songs(
    request: Request,
    song: str = Query(..., description="Song name to search for"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Search for songs on YouTube.
    
    Returns a list of matching songs with metadata including title, duration, 
    thumbnail, uploader, view count, and video ID.
    """
    try:
        logger.info(f"Search request received for: {song}")
        
        # Check cache
        cache_key = f"search:{song}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for search: {song}")
            return cached

        # Perform search
        logger.info("Calling extractor.search")
        results = await extractor.search(song, max_results=10)
        logger.info(f"Extractor returned {len(results)} results")
        
        if not results:
            logger.warning(f"No results from extractor for: {song}")
            raise HTTPException(status_code=404, detail="No results found")

        # Cache results
        await cache.set(cache_key, results)
        
        # Increment stats
        await cache.increment("stats:search_requests")
        await cache.increment("stats:successful_requests")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/play", response_model=SearchResult)
@limiter.limit("100/minute")
async def play_song(
    request: Request,
    song: str = Query(..., description="Song name to play"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Get direct audio information for a song.
    
    Returns the first search result with all metadata needed for playback.
    """
    try:
        # Check cache
        cache_key = f"play:{song}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for play: {song}")
            return cached

        # Perform search
        results = await extractor.search(song, max_results=1)
        
        if not results or not results[0]:
            raise HTTPException(status_code=404, detail="Song not found")

        result = results[0]
        
        # Cache result
        await cache.set(cache_key, result)
        
        # Increment stats
        await cache.increment("stats:play_requests")
        await cache.increment("stats:successful_requests")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Play error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Failed to get song information")


@router.get("/lyrics", response_model=LyricsResponse)
@limiter.limit("50/minute")
async def get_lyrics(
    request: Request,
    song: str = Query(..., description="Song name to get lyrics for"),
    api_key: Optional[str] = Depends(get_optional_api_key)
):
    """
    Get lyrics for a song.
    
    Returns lyrics if available from video captions or auto-generated captions.
    """
    try:
        # Check cache
        cache_key = f"lyrics:{song}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for lyrics: {song}")
            return cached

        # Get lyrics
        lyrics = await extractor.get_lyrics(song)
        
        if not lyrics:
            raise HTTPException(status_code=404, detail="Lyrics not found")

        result = {
            "lyrics": lyrics,
            "source": "youtube_captions"
        }
        
        # Cache result
        await cache.set(cache_key, result, ttl=7200)  # 2 hours for lyrics
        
        # Increment stats
        await cache.increment("stats:lyrics_requests")
        await cache.increment("stats:successful_requests")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Lyrics error: {str(e)}")
        await cache.increment("stats:failed_requests")
        raise HTTPException(status_code=500, detail="Failed to get lyrics")


@router.post("/generate-key")
@limiter.limit("5/minute")
async def generate_api_key_public(
    plan: str = "free",
    request: Request = None
):
    """
    Public endpoint to generate API key without authentication.
    """
    try:
        # Generate random API key
        api_key_value = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        # Set plan limits
        plan_limits = {
            "free": {"daily_limit": 100, "monthly_limit": 3000},
            "pro": {"daily_limit": 10000, "monthly_limit": 300000},
            "enterprise": {"daily_limit": -1, "monthly_limit": -1}
        }
        
        if plan not in plan_limits:
            raise HTTPException(status_code=400, detail="Invalid plan")
        
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
