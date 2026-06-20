from fastapi import APIRouter, HTTPException, Query, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
from loguru import logger

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
        # Check cache
        cache_key = f"search:{song}"
        cached = await cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for search: {song}")
            return cached

        # Perform search
        results = await extractor.search(song, max_results=10)
        
        if not results:
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
