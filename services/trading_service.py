"""
Trading service - handles orders, positions, and trade execution
"""
import logging
import MetaTrader5 as mt5
import pandas as pd
from typing import List, Optional

from core.mt5_connection import mt5_connection
from core.exceptions import (
    InvalidOrderError,
    OrderExecutionError,
    PositionNotFoundError,
    MT5Exception
)

logger = logging.getLogger(__name__)


class TradingService:
    """Service for trading operations"""

    def get_account_info(self) -> dict:
        """
        Get account information

        Returns:
            Account information dictionary
        """
        mt5_connection.ensure_connection()

        info = mt5.account_info()
        if info is None:
            raise MT5Exception("Failed to get account information")

        return info._asdict()

    def send_market_order(
        self,
        symbol: str,
        volume: float,
        order_type: str,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        deviation: int = 20,
        magic: int = 0,
        comment: str = ""
    ) -> dict:
        """
        Send a market order

        Args:
            symbol: Trading symbol
            volume: Order volume in lots
            order_type: "BUY" or "SELL"
            sl: Stop Loss price (optional)
            tp: Take Profit price (optional)
            deviation: Maximum price deviation in points
            magic: Magic number for order identification
            comment: Order comment

        Returns:
            Order result dictionary

        Raises:
            InvalidOrderError: If order parameters are invalid
            OrderExecutionError: If order execution fails
        """
        mt5_connection.ensure_connection()

        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise InvalidOrderError(f"Failed to get price for symbol {symbol}")

        # Determine order type and price
        if order_type.upper() == "BUY":
            mt5_order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif order_type.upper() == "SELL":
            mt5_order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            raise InvalidOrderError(f"Invalid order type: {order_type}")

        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "deviation": deviation,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Add SL/TP if provided
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp

        logger.info(f"Sending market order: {order_type} {volume} {symbol}")

        # Send order
        result = mt5.order_send(request)
        if result is None:
            raise OrderExecutionError("Order send returned None")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_code, error_msg = mt5.last_error()
            raise OrderExecutionError(
                f"Order failed: {result.comment} (MT5 error: {error_msg})",
                code=result.retcode
            )

        logger.info(f"Order executed successfully: {result.order}")

        return result._asdict()

    def get_positions(self, magic: Optional[int] = None) -> List[dict]:
        """
        Get all open positions

        Args:
            magic: Filter by magic number (optional)

        Returns:
            List of position dictionaries
        """
        mt5_connection.ensure_connection()

        if magic is not None:
            positions = mt5.positions_get(magic=magic)
        else:
            positions = mt5.positions_get()

        if positions is None:
            return []

        result = []
        for position in positions:
            pos_dict = position._asdict()
            # Add type string
            pos_dict["type_str"] = "BUY" if position.type == mt5.ORDER_TYPE_BUY else "SELL"
            result.append(pos_dict)

        return result

    def get_position_by_ticket(self, ticket: int) -> dict:
        """
        Get a specific position by ticket

        Args:
            ticket: Position ticket/ID

        Returns:
            Position dictionary

        Raises:
            PositionNotFoundError: If position not found
        """
        positions = self.get_positions()

        for position in positions:
            if position["ticket"] == ticket:
                return position

        raise PositionNotFoundError(f"Position {ticket} not found")

    def close_position(
        self,
        position_id: int,
        volume: Optional[float] = None,
        deviation: int = 20
    ) -> dict:
        """
        Close a position

        Args:
            position_id: Position ticket/ID
            volume: Volume to close (None for full close)
            deviation: Maximum price deviation in points

        Returns:
            Close result dictionary

        Raises:
            PositionNotFoundError: If position not found
            OrderExecutionError: If close fails
        """
        mt5_connection.ensure_connection()

        # Get position info
        position = self.get_position_by_ticket(position_id)

        # Determine close volume
        close_volume = volume if volume is not None else position["volume"]

        # Determine close type (opposite of position type)
        if position["type"] == mt5.ORDER_TYPE_BUY:
            close_type = mt5.ORDER_TYPE_SELL
        else:
            close_type = mt5.ORDER_TYPE_BUY

        # Get current price
        tick = mt5.symbol_info_tick(position["symbol"])
        if tick is None:
            raise OrderExecutionError(f"Failed to get price for {position['symbol']}")

        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        # Prepare close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position["symbol"],
            "volume": close_volume,
            "type": close_type,
            "position": position_id,
            "price": price,
            "deviation": deviation,
            "magic": position["magic"],
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        logger.info(f"Closing position {position_id}")

        # Send close order
        result = mt5.order_send(request)
        if result is None:
            raise OrderExecutionError("Close order returned None")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_code, error_msg = mt5.last_error()
            raise OrderExecutionError(
                f"Close failed: {result.comment} (MT5 error: {error_msg})",
                code=result.retcode
            )

        logger.info(f"Position {position_id} closed successfully")

        return result._asdict()

    def modify_position(
        self,
        position_id: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> dict:
        """
        Modify position SL/TP

        Args:
            position_id: Position ticket/ID
            sl: New Stop Loss price (optional)
            tp: New Take Profit price (optional)

        Returns:
            Modify result dictionary

        Raises:
            PositionNotFoundError: If position not found
            OrderExecutionError: If modification fails
        """
        mt5_connection.ensure_connection()

        # Verify position exists
        position = self.get_position_by_ticket(position_id)

        # Prepare modify request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position_id,
            "symbol": position["symbol"],
        }

        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp

        if sl is None and tp is None:
            raise InvalidOrderError("At least one of SL or TP must be provided")

        logger.info(f"Modifying position {position_id}")

        # Send modify request
        result = mt5.order_send(request)
        if result is None:
            raise OrderExecutionError("Modify order returned None")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_code, error_msg = mt5.last_error()
            raise OrderExecutionError(
                f"Modification failed: {result.comment} (MT5 error: {error_msg})",
                code=result.retcode
            )

        logger.info(f"Position {position_id} modified successfully")

        return result._asdict()

    def close_all_positions(
        self,
        order_type: str = "all",
        magic: Optional[int] = None
    ) -> List[dict]:
        """
        Close all open positions

        Args:
            order_type: Filter by type ("BUY", "SELL", or "all")
            magic: Filter by magic number (optional)

        Returns:
            List of close result dictionaries
        """
        positions = self.get_positions(magic=magic)

        # Filter by type if specified
        if order_type.upper() != "ALL":
            if order_type.upper() == "BUY":
                positions = [p for p in positions if p["type"] == mt5.ORDER_TYPE_BUY]
            elif order_type.upper() == "SELL":
                positions = [p for p in positions if p["type"] == mt5.ORDER_TYPE_SELL]

        results = []
        for position in positions:
            try:
                result = self.close_position(position["ticket"])
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to close position {position['ticket']}: {e}")

        return results

    def get_positions_total(self) -> int:
        """
        Get total number of open positions

        Returns:
            Number of open positions
        """
        mt5_connection.ensure_connection()

        total = mt5.positions_total()
        return total if total is not None else 0


# Global instance
trading_service = TradingService()
