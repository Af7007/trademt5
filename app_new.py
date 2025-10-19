"""
MetaTrader5 API - Main Application
Modern Flask-based REST API serving as middleware between MT5 and frontend
"""
import logging
import os
import sys
import threading
import time
from flask import Flask, jsonify
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports
from core.config import settings
from core.mt5_connection import mt5_connection
from core.exceptions import MT5Exception

# Middleware imports
from api.middleware.cors import setup_cors
from api.middleware.error_handler import setup_error_handlers

# API routes
from api.v1 import v1_bp

# WebSocket
from api.v1.routes.websocket import init_socketio

# Legacy routes (optional - keep for backwards compatibility)
from routes.health import health_bp

# Scalping bot
from scalping_bot import ScalpingBot
import MetaTrader5 as mt5

# Configure logging
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scalping bot instance
scalping_bot_instance = None


def create_app():
    """
    Application factory pattern

    Returns:
        Configured Flask application
    """
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['JSON_SORT_KEYS'] = False

    # Proxy fix for running behind Traefik
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Setup CORS
    setup_cors(app)

    # Setup error handlers
    setup_error_handlers(app)

    # Swagger/OpenAPI documentation
    swagger_config = {
        "swagger": "2.0",
        "info": {
            "title": settings.APP_NAME,
            "description": "REST API for MetaTrader5 trading platform. Provides endpoints for market data, trading operations, account management, and strategy execution.",
            "version": settings.APP_VERSION,
            "contact": {
                "name": "API Support",
                "url": "https://github.com/your-repo"
            }
        },
        "basePath": "/",
        "schemes": ["https", "http"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
            },
            "ApiKey": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header",
                "description": "API Key for authentication"
            }
        },
        "specs": [{
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }
    Swagger(app, config=swagger_config)

    # Register API v1 routes
    app.register_blueprint(v1_bp, url_prefix=settings.API_V1_PREFIX)

    # Register legacy health check (backwards compatibility)
    app.register_blueprint(health_bp)

    # Add root endpoint
    @app.route('/')
    def root():
        """API root endpoint"""
        return jsonify({
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "documentation": "/apidocs/",
            "api": {
                "v1": settings.API_V1_PREFIX
            },
            "websocket": {
                "enabled": True,
                "path": "/socket.io"
            }
        }), 200

    # Add health endpoint
    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        from datetime import datetime

        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "mt5": {
                "initialized": mt5_connection.is_initialized,
                "logged_in": mt5_connection.is_logged_in,
                "version": mt5_connection.get_version()
            },
            "services": {
                "cache": settings.REDIS_ENABLED,
                "rate_limiting": settings.RATE_LIMIT_ENABLED
            }
        }

        return jsonify(health_status), 200

    return app


def initialize_mt5():
    """Initialize MT5 connection"""
    try:
        logger.info("=" * 60)
        logger.info("Initializing MetaTrader5 connection...")
        logger.info("=" * 60)

        mt5_connection.initialize()

        logger.info("MT5 initialized successfully")
        logger.info(f"MT5 Version: {mt5_connection.get_version()}")

        if mt5_connection.is_logged_in:
            account_info = mt5_connection.get_account_info()
            logger.info(f"Logged in to account: {account_info.get('login')}")
            logger.info(f"Server: {account_info.get('server')}")
            logger.info(f"Balance: {account_info.get('balance')} {account_info.get('currency')}")

    except MT5Exception as e:
        logger.error(f"Failed to initialize MT5: {e}")
        if settings.DEBUG:
            raise
        else:
            logger.warning("Continuing without MT5 connection...")


def start_scalping_bot_background():
    """
    Start scalping bot in background thread
    """
    global scalping_bot_instance

    # Wait for MT5 initialization
    time.sleep(5)

    try:
        logger.info("=" * 60)
        logger.info("Starting Scalping Bot...")
        logger.info("=" * 60)

        scalping_bot_instance = ScalpingBot(
            symbol=settings.SCALPING_SYMBOL,
            timeframe=mt5.TIMEFRAME_M5,
            confidence_threshold=settings.SCALPING_CONFIDENCE_THRESHOLD,
            volume=settings.SCALPING_VOLUME
        )

        logger.info(f"Scalping Bot Configuration:")
        logger.info(f"  Symbol: {settings.SCALPING_SYMBOL}")
        logger.info(f"  Timeframe: M5")
        logger.info(f"  Confidence Threshold: {settings.SCALPING_CONFIDENCE_THRESHOLD}%")
        logger.info(f"  Volume: {settings.SCALPING_VOLUME}")
        logger.info(f"  Check Interval: {settings.SCALPING_INTERVAL}s")

        # Run bot
        scalping_bot_instance.run(interval=settings.SCALPING_INTERVAL)

    except Exception as e:
        logger.error(f"Error starting scalping bot: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    # Create Flask app
    app = create_app()

    # Initialize WebSocket
    socketio = init_socketio(app)

    # Initialize MT5
    initialize_mt5()

    # Start scalping bot in background (optional)
    if os.getenv("ENABLE_SCALPING_BOT", "false").lower() == "true":
        bot_thread = threading.Thread(
            target=start_scalping_bot_background,
            daemon=True
        )
        bot_thread.start()
        logger.info("Scalping bot thread started")
    else:
        logger.info("Scalping bot disabled (set ENABLE_SCALPING_BOT=true to enable)")

    # Display startup info
    logger.info("=" * 60)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Host: {settings.HOST}:{settings.PORT}")
    logger.info(f"API v1: {settings.API_V1_PREFIX}")
    logger.info(f"Documentation: http://{settings.HOST}:{settings.PORT}/apidocs/")
    logger.info(f"WebSocket: Enabled")
    logger.info(f"CORS Origins: {', '.join(settings.CORS_ORIGINS)}")
    logger.info(f"Rate Limiting: {'Enabled' if settings.RATE_LIMIT_ENABLED else 'Disabled'}")
    logger.info(f"Redis Cache: {'Enabled' if settings.REDIS_ENABLED else 'Disabled'}")
    logger.info("=" * 60)

    # Run the application with SocketIO
    socketio.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG,
        use_reloader=False  # Disable reloader to prevent duplicate threads
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        mt5_connection.shutdown()
        logger.info("Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
