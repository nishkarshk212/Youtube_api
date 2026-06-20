from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
from loguru import logger
from app.config import settings
from app.cache import cache


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """Verify API key"""
    # If no API keys are configured, allow all requests (development mode)
    if not settings.api_keys_list:
        return "dev"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
        )

    if api_key not in settings.api_keys_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    # Increment request count for this API key
    await cache.increment(f"api_key:{api_key}:requests")

    return api_key


async def get_optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """Get optional API key (for public endpoints)"""
    if api_key and settings.api_keys_list and api_key in settings.api_keys_list:
        await cache.increment(f"api_key:{api_key}:requests")
        return api_key
    return None
