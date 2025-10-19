"""
Market data service - handles symbol info, ticks, candles, etc.
"""
import logging
import MetaTrader5 as mt5
import pandas as pd
from typing import List, Optional
from datetime import datetime
import pytz

from core.mt5_connection import mt5_connection
from core.exceptions import SymbolNotFoundError, MT5Exception
from core.config import settings
from .cache_service import cache_service
from lib import get_timeframe

logger = logging.getLogger(__name__)


class MarketService:
    """Service for market data operations"""

    def __init__(self):
        self.cache = cache_service

    def get_symbols(self) -> List[dict]:
        """
        Get list of all available symbols

        Returns:
            List of symbol information dictionaries
        """
        mt5_connection.ensure_connection()

        # Try cache first
        cache_key = "symbols:all"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Returning symbols from cache")
            return cached

        symbols = mt5.symbols_get()
        if symbols is None:
            raise MT5Exception("Failed to get symbols")

        result = []
        for symbol in symbols:
            symbol_dict = symbol._asdict()
            # Filter out internal fields
            result.append({
                "name": symbol_dict["name"],
                "description": symbol_dict.get("description", ""),
                "path": symbol_dict.get("path", ""),
                "visible": symbol_dict.get("visible", False),
                "digits": symbol_dict.get("digits", 0),
                "point": symbol_dict.get("point", 0),
                "spread": symbol_dict.get("spread", 0),
                "volume_min": symbol_dict.get("volume_min", 0),
                "volume_max": symbol_dict.get("volume_max", 0),
                "volume_step": symbol_dict.get("volume_step", 0),
                "trade_mode": symbol_dict.get("trade_mode", 0),
            })

        # Cache for 1 hour
        self.cache.set(cache_key, result, ttl=settings.CACHE_TTL_SYMBOLS)

        return result

    def get_symbol_info(self, symbol: str) -> dict:
        """
        Get detailed information about a specific symbol

        Args:
            symbol: Symbol name

        Returns:
            Symbol information dictionary

        Raises:
            SymbolNotFoundError: If symbol not found
        """
        mt5_connection.ensure_connection()

        # Try cache first
        cache_key = f"symbol:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"Returning symbol {symbol} from cache")
            return cached

        info = mt5.symbol_info(symbol)
        if info is None:
            raise SymbolNotFoundError(f"Symbol {symbol} not found")

        result = info._asdict()

        # Cache for 1 hour
        self.cache.set(cache_key, result, ttl=settings.CACHE_TTL_SYMBOLS)

        return result

    def get_tick(self, symbol: str) -> dict:
        """
        Get latest tick for a symbol

        Args:
            symbol: Symbol name

        Returns:
            Tick information dictionary

        Raises:
            SymbolNotFoundError: If symbol not found
        """
        mt5_connection.ensure_connection()

        # Try cache first
        cache_key = f"tick:{symbol}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise SymbolNotFoundError(f"Failed to get tick for symbol {symbol}")

        result = tick._asdict()

        # Cache for 1 second
        self.cache.set(cache_key, result, ttl=settings.CACHE_TTL_TICK)

        return result

    def get_candles(
        self,
        symbol: str,
        timeframe: str = "M1",
        count: int = 100,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[dict]:
        """
        Get candle data for a symbol

        Args:
            symbol: Symbol name
            timeframe: Timeframe string (M1, M5, H1, etc.)
            count: Number of candles to fetch
            from_date: Start date (optional)
            to_date: End date (optional)

        Returns:
            List of candle dictionaries

        Raises:
            SymbolNotFoundError: If symbol not found or no data
        """
        mt5_connection.ensure_connection()

        mt5_timeframe = get_timeframe(timeframe)

        if from_date and to_date:
            # Fetch by date range
            utc = pytz.UTC
            if from_date.tzinfo is None:
                from_date = utc.localize(from_date)
            if to_date.tzinfo is None:
                to_date = utc.localize(to_date)

            rates = mt5.copy_rates_range(symbol, mt5_timeframe, from_date, to_date)
        else:
            # Fetch by count
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)

        if rates is None or len(rates) == 0:
            raise SymbolNotFoundError(f"Failed to get candle data for {symbol}")

        # Convert to DataFrame and then to dict
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        return df.to_dict(orient='records')

    def search_symbols(self, query: str) -> List[dict]:
        """
        Search symbols by name or description

        Args:
            query: Search query

        Returns:
            List of matching symbols
        """
        all_symbols = self.get_symbols()

        query_lower = query.lower()
        results = [
            s for s in all_symbols
            if query_lower in s["name"].lower() or
            query_lower in s.get("description", "").lower()
        ]

        return results

    def enable_symbol(self, symbol: str) -> bool:
        """
        Enable a symbol for trading

        Args:
            symbol: Symbol name

        Returns:
            True if successful
        """
        mt5_connection.ensure_connection()

        if not mt5.symbol_select(symbol, True):
            logger.error(f"Failed to enable symbol {symbol}")
            return False

        logger.info(f"Symbol {symbol} enabled")
        return True


# Global instance
market_service = MarketService()
