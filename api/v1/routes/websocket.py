"""
WebSocket routes for real-time data streaming
"""
import logging
from flask import Blueprint
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import MetaTrader5 as mt5
import time
from threading import Thread, Event

from api.middleware.auth import verify_token, verify_api_key
from core.mt5_connection import mt5_connection
from services.market_service import market_service

logger = logging.getLogger(__name__)

websocket_bp = Blueprint('websocket', __name__)

# Global SocketIO instance (will be initialized in app.py)
socketio: SocketIO = None

# Active subscriptions tracking
active_subscriptions = {}
subscription_threads = {}
stop_events = {}


def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    global socketio
    from flask_socketio import SocketIO as FlaskSocketIO

    socketio = FlaskSocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=False
    )

    register_socketio_handlers(socketio)
    return socketio


def verify_ws_auth(auth_data):
    """Verify WebSocket authentication"""
    if not auth_data:
        return False

    token = auth_data.get('token')
    if not token:
        return False

    # Try JWT verification
    payload = verify_token(token)
    if payload:
        return True

    # Try API key verification
    if verify_api_key(token):
        return True

    return False


def stream_tick_data(symbol: str, room: str, stop_event: Event):
    """
    Stream tick data for a symbol to a WebSocket room

    Args:
        symbol: Trading symbol
        room: WebSocket room name
        stop_event: Event to signal stopping
    """
    logger.info(f"Starting tick stream for {symbol} in room {room}")

    while not stop_event.is_set():
        try:
            mt5_connection.ensure_connection()

            # Get latest tick
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                tick_data = {
                    "symbol": symbol,
                    "time": tick.time,
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "last": tick.last,
                    "volume": tick.volume,
                    "spread": tick.ask - tick.bid if tick.ask and tick.bid else 0
                }

                # Emit to room
                if socketio:
                    socketio.emit('tick_update', tick_data, room=room)

            # Sleep for 1 second
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error streaming tick for {symbol}: {e}")
            time.sleep(5)  # Wait before retry

    logger.info(f"Stopped tick stream for {symbol} in room {room}")


def register_socketio_handlers(sio: SocketIO):
    """Register all WebSocket event handlers"""

    @sio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        logger.info(f"Client connecting with auth: {auth}")

        # Authentication is optional for basic connections
        # but required for subscribing to data
        logger.info("Client connected")
        emit('connected', {'message': 'Connected to MT5 WebSocket server'})

    @sio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("Client disconnected")

        # Clean up any active subscriptions for this client
        # (This is simplified - in production, track subscriptions per client)

    @sio.on('subscribe_tick')
    def handle_subscribe_tick(data):
        """
        Subscribe to tick updates for a symbol

        Expected data: {
            'symbol': 'BTCUSDc',
            'token': 'jwt_token_or_api_key'
        }
        """
        logger.info(f"Subscribe tick request: {data}")

        # Verify authentication
        if not verify_ws_auth(data):
            emit('error', {'message': 'Authentication required'})
            disconnect()
            return

        symbol = data.get('symbol')
        if not symbol:
            emit('error', {'message': 'Symbol is required'})
            return

        # Create room for this symbol
        room = f"tick_{symbol}"
        join_room(room)

        # Start streaming if not already active
        if room not in active_subscriptions:
            active_subscriptions[room] = set()
            stop_event = Event()
            stop_events[room] = stop_event

            # Start background thread for streaming
            thread = Thread(
                target=stream_tick_data,
                args=(symbol, room, stop_event),
                daemon=True
            )
            thread.start()
            subscription_threads[room] = thread

        # Track this client's subscription
        # (In production, use request.sid to track individual clients)
        active_subscriptions[room].add('client')  # Simplified

        emit('subscribed', {
            'symbol': symbol,
            'message': f'Subscribed to tick updates for {symbol}'
        })

        logger.info(f"Client subscribed to {symbol}")

    @sio.on('unsubscribe_tick')
    def handle_unsubscribe_tick(data):
        """
        Unsubscribe from tick updates

        Expected data: {
            'symbol': 'BTCUSDc'
        }
        """
        symbol = data.get('symbol')
        if not symbol:
            emit('error', {'message': 'Symbol is required'})
            return

        room = f"tick_{symbol}"
        leave_room(room)

        # Remove from active subscriptions
        if room in active_subscriptions:
            active_subscriptions[room].discard('client')

            # Stop streaming if no more subscribers
            if len(active_subscriptions[room]) == 0:
                if room in stop_events:
                    stop_events[room].set()
                    del stop_events[room]
                if room in subscription_threads:
                    del subscription_threads[room]
                del active_subscriptions[room]

        emit('unsubscribed', {
            'symbol': symbol,
            'message': f'Unsubscribed from tick updates for {symbol}'
        })

        logger.info(f"Client unsubscribed from {symbol}")

    @sio.on('ping')
    def handle_ping():
        """Handle ping for keepalive"""
        emit('pong', {'timestamp': time.time()})


# Export socketio instance getter
def get_socketio():
    """Get the global SocketIO instance"""
    return socketio
