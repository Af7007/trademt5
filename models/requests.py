"""
Request models for API endpoints
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class MarketOrderRequest(BaseModel):
    """Request model for creating a market order"""

    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDc)")
    volume: float = Field(..., gt=0, description="Order volume in lots")
    order_type: Literal["BUY", "SELL"] = Field(..., description="Order type")
    sl: Optional[float] = Field(None, description="Stop Loss price")
    tp: Optional[float] = Field(None, description="Take Profit price")
    deviation: int = Field(20, ge=0, description="Maximum price deviation in points")
    magic: int = Field(0, ge=0, description="Magic number for order identification")
    comment: str = Field("", max_length=50, description="Order comment")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTCUSDc",
                "volume": 0.01,
                "order_type": "BUY",
                "sl": 45000.0,
                "tp": 50000.0,
                "magic": 12345,
                "comment": "API order"
            }
        }


class ModifyPositionRequest(BaseModel):
    """Request model for modifying a position"""

    position_id: int = Field(..., description="Position ticket/ID")
    sl: Optional[float] = Field(None, description="New Stop Loss price")
    tp: Optional[float] = Field(None, description="New Take Profit price")

    @validator('sl', 'tp')
    def check_at_least_one(cls, v, values):
        if 'sl' in values and values['sl'] is None and v is None:
            raise ValueError('At least one of sl or tp must be provided')
        return v

    class Config:
        schema_extra = {
            "example": {
                "position_id": 123456,
                "sl": 45000.0,
                "tp": 50000.0
            }
        }


class ClosePositionRequest(BaseModel):
    """Request model for closing a position"""

    position_id: int = Field(..., description="Position ticket/ID to close")
    volume: Optional[float] = Field(None, gt=0, description="Volume to close (None for full close)")
    deviation: int = Field(20, ge=0, description="Maximum price deviation in points")

    class Config:
        schema_extra = {
            "example": {
                "position_id": 123456,
                "volume": 0.01,
                "deviation": 20
            }
        }


class CandlesRequest(BaseModel):
    """Request model for fetching candle data"""

    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field("M1", description="Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)")
    count: int = Field(100, ge=1, le=10000, description="Number of candles to fetch")
    from_date: Optional[datetime] = Field(None, description="Start date (optional)")
    to_date: Optional[datetime] = Field(None, description="End date (optional)")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTCUSDc",
                "timeframe": "M5",
                "count": 100
            }
        }


class ScalpingBotRequest(BaseModel):
    """Request model for scalping bot configuration"""

    symbol: str = Field("BTCUSDc", description="Trading symbol")
    timeframe: str = Field("M5", description="Timeframe for analysis")
    confidence_threshold: int = Field(85, ge=0, le=100, description="Confidence threshold (0-100)")
    volume: float = Field(0.01, gt=0, description="Order volume in lots")
    interval: int = Field(60, ge=10, description="Check interval in seconds")
    enabled: bool = Field(True, description="Enable/disable the bot")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "BTCUSDc",
                "timeframe": "M5",
                "confidence_threshold": 85,
                "volume": 0.01,
                "interval": 60,
                "enabled": True
            }
        }


class LoginRequest(BaseModel):
    """Request model for API authentication"""

    username: str = Field(..., description="Username or API key")
    password: str = Field(..., description="Password or secret")

    class Config:
        schema_extra = {
            "example": {
                "username": "trader123",
                "password": "secure_password"
            }
        }
