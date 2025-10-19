"""
Response models for API endpoints
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str = Field(..., description="Error message")
    code: Optional[int] = Field(None, description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")

    class Config:
        schema_extra = {
            "example": {
                "error": "Symbol not found",
                "code": 404,
                "details": {"symbol": "INVALID"}
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response"""

    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")

    class Config:
        schema_extra = {
            "example": {
                "message": "Operation successful",
                "data": {}
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status")
    mt5_initialized: bool = Field(..., description="MT5 initialization status")
    mt5_logged_in: bool = Field(..., description="MT5 login status")
    version: Optional[str] = Field(None, description="MT5 version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "mt5_initialized": True,
                "mt5_logged_in": True,
                "version": "5.0.3880",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }


class SymbolInfo(BaseModel):
    """Symbol information"""

    name: str
    description: Optional[str] = None
    bid: float
    ask: float
    spread: int
    digits: int
    point: float
    volume_min: float
    volume_max: float
    volume_step: float
    trade_mode: int


class TickInfo(BaseModel):
    """Tick information"""

    symbol: str
    time: datetime
    bid: float
    ask: float
    last: float
    volume: int
    spread: int


class CandleData(BaseModel):
    """OHLCV candle data"""

    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


class AccountInfo(BaseModel):
    """Account information"""

    login: int
    name: str
    server: str
    currency: str
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    leverage: int
    trade_allowed: bool
    trade_expert: bool


class Position(BaseModel):
    """Open position information"""

    ticket: int
    time: datetime
    type: int
    type_str: str
    magic: int
    symbol: str
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    swap: float
    comment: str


class OrderResult(BaseModel):
    """Order execution result"""

    retcode: int
    retcode_str: str
    deal: int
    order: int
    volume: float
    price: float
    comment: str
    request_id: int


class StrategyStatus(BaseModel):
    """Strategy/bot status"""

    name: str
    enabled: bool
    running: bool
    symbol: str
    timeframe: str
    trades_count: int
    profit: float
    last_signal: Optional[str] = None
    last_check: Optional[datetime] = None


class SymbolListResponse(BaseModel):
    """List of available symbols"""

    symbols: List[SymbolInfo]
    count: int


class PositionListResponse(BaseModel):
    """List of open positions"""

    positions: List[Position]
    count: int
    total_profit: float


class CandleListResponse(BaseModel):
    """List of candles"""

    candles: List[CandleData]
    count: int
    symbol: str
    timeframe: str


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }
