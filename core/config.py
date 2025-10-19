"""
Centralized configuration management
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings"""

    # Application
    APP_NAME: str = "MetaTrader5 API"
    APP_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("MT5_API_PORT", "5001"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    API_KEY: Optional[str] = os.getenv("API_KEY")

    # CORS
    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001"
    ).split(",")

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "True").lower() == "true"

    # Cache TTL (seconds)
    CACHE_TTL_SYMBOLS: int = 3600  # 1 hour
    CACHE_TTL_TICK: int = 1  # 1 second
    CACHE_TTL_ACCOUNT: int = 5  # 5 seconds

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # MT5
    MT5_LOGIN: Optional[int] = os.getenv("MT5_LOGIN")
    MT5_PASSWORD: Optional[str] = os.getenv("MT5_PASSWORD")
    MT5_SERVER: Optional[str] = os.getenv("MT5_SERVER")
    MT5_TIMEOUT: int = int(os.getenv("MT5_TIMEOUT", "60000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"  # json or text

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MAX_CONNECTIONS: int = 100

    # Scalping Bot (default settings)
    SCALPING_SYMBOL: str = os.getenv("SCALPING_SYMBOL", "BTCUSDc")
    SCALPING_TIMEFRAME: str = os.getenv("SCALPING_TIMEFRAME", "M5")
    SCALPING_CONFIDENCE_THRESHOLD: int = int(os.getenv("SCALPING_CONFIDENCE_THRESHOLD", "85"))
    SCALPING_VOLUME: float = float(os.getenv("SCALPING_VOLUME", "0.01"))
    SCALPING_INTERVAL: int = int(os.getenv("SCALPING_INTERVAL", "60"))


settings = Settings()
