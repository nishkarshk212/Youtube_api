from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: str = "8000"
    API_KEY_SECRET: str = "your-secret-key-change-this"
    ENVIRONMENT: str = "development"

    @field_validator('API_PORT', mode='before')
    @classmethod
    def parse_port(cls, v):
        if isinstance(v, str):
            try:
                return str(int(v))
            except ValueError:
                return "8000"
        return str(v)

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60

    # Proxy Configuration
    HTTP_PROXY: Optional[str] = None
    HTTPS_PROXY: Optional[str] = None
    PROXY_LIST: Optional[str] = None

    # Cache Configuration
    CACHE_TTL: int = 3600
    ENABLE_CACHE: bool = True

    # API Keys
    API_KEYS: str = ""

    # Fallback Servers
    FALLBACK_SERVERS: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def api_keys_list(self) -> List[str]:
        return [key.strip() for key in self.API_KEYS.split(",") if key.strip()]

    @property
    def fallback_servers_list(self) -> List[str]:
        return [server.strip() for server in self.FALLBACK_SERVERS.split(",") if server.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
