"""
Trading strategies and bots routes
"""
from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from

from api.middleware.auth import auth_required
from api.middleware.rate_limit import rate_limit
from models.requests import ScalpingBotRequest

strategies_bp = Blueprint('strategies', __name__)


@strategies_bp.route('/', methods=['GET'])
@auth_required
@swag_from({
    'tags': ['Strategies'],
    'summary': 'List available strategies',
    'description': 'Get list of all available trading strategies/bots',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {
            'description': 'List of strategies',
            'schema': {
                'type': 'object',
                'properties': {
                    'strategies': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'description': {'type': 'string'},
                                'enabled': {'type': 'boolean'}
                            }
                        }
                    }
                }
            }
        },
        401: {'description': 'Unauthorized'}
    }
})
def list_strategies():
    """List available strategies"""
    strategies = [
        {
            "name": "scalping",
            "description": "Scalping bot with pattern analysis",
            "enabled": True,
            "endpoint": "/api/v1/strategies/scalping"
        }
    ]

    return jsonify({"strategies": strategies, "count": len(strategies)}), 200


@strategies_bp.route('/scalping/status', methods=['GET'])
@auth_required
@swag_from({
    'tags': ['Strategies'],
    'summary': 'Get scalping bot status',
    'description': 'Retrieve current status of the scalping bot',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {'description': 'Scalping bot status'},
        401: {'description': 'Unauthorized'}
    }
})
def get_scalping_status():
    """Get scalping bot status"""
    # Access the global scalping bot instance
    from app import scalping_bot_instance

    if scalping_bot_instance is None:
        return jsonify({
            "name": "scalping",
            "running": False,
            "enabled": False,
            "message": "Bot not initialized"
        }), 200

    # Get bot statistics
    status = {
        "name": "scalping",
        "running": scalping_bot_instance.running if hasattr(scalping_bot_instance, 'running') else False,
        "enabled": True,
        "symbol": scalping_bot_instance.symbol if hasattr(scalping_bot_instance, 'symbol') else None,
        "timeframe": str(scalping_bot_instance.timeframe) if hasattr(scalping_bot_instance, 'timeframe') else None,
        "confidence_threshold": scalping_bot_instance.confidence_threshold if hasattr(scalping_bot_instance, 'confidence_threshold') else None,
        "volume": scalping_bot_instance.volume if hasattr(scalping_bot_instance, 'volume') else None,
    }

    return jsonify(status), 200


@strategies_bp.route('/scalping/start', methods=['POST'])
@auth_required
@swag_from({
    'tags': ['Strategies'],
    'summary': 'Start scalping bot',
    'description': 'Start the scalping bot with specified configuration',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True
        },
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'symbol': {'type': 'string', 'default': 'BTCUSDc'},
                    'timeframe': {'type': 'string', 'default': 'M5'},
                    'confidence_threshold': {'type': 'integer', 'default': 85},
                    'volume': {'type': 'number', 'default': 0.01},
                    'interval': {'type': 'integer', 'default': 60}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Bot started successfully'},
        400: {'description': 'Bot already running or invalid configuration'},
        401: {'description': 'Unauthorized'}
    }
})
def start_scalping():
    """Start scalping bot"""
    # This would require refactoring the scalping bot to support start/stop
    # For now, return a message indicating the bot is auto-started
    return jsonify({
        "message": "Scalping bot is auto-started on application startup",
        "note": "To configure, use environment variables or restart the application"
    }), 200


@strategies_bp.route('/scalping/stop', methods=['POST'])
@auth_required
@swag_from({
    'tags': ['Strategies'],
    'summary': 'Stop scalping bot',
    'description': 'Stop the running scalping bot',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {'description': 'Bot stopped successfully'},
        400: {'description': 'Bot not running'},
        401: {'description': 'Unauthorized'}
    }
})
def stop_scalping():
    """Stop scalping bot"""
    # This would require refactoring the scalping bot to support start/stop
    return jsonify({
        "message": "Stop functionality not yet implemented",
        "note": "Bot runs as a background daemon. Restart the application to stop it."
    }), 200


@strategies_bp.route('/scalping/config', methods=['GET'])
@auth_required
@swag_from({
    'tags': ['Strategies'],
    'summary': 'Get scalping bot configuration',
    'description': 'Retrieve current configuration of the scalping bot',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {'description': 'Bot configuration'},
        401: {'description': 'Unauthorized'}
    }
})
def get_scalping_config():
    """Get scalping bot configuration"""
    from app import scalping_bot_instance
    from core.config import settings

    if scalping_bot_instance:
        config = {
            "symbol": scalping_bot_instance.symbol if hasattr(scalping_bot_instance, 'symbol') else settings.SCALPING_SYMBOL,
            "timeframe": str(scalping_bot_instance.timeframe) if hasattr(scalping_bot_instance, 'timeframe') else settings.SCALPING_TIMEFRAME,
            "confidence_threshold": scalping_bot_instance.confidence_threshold if hasattr(scalping_bot_instance, 'confidence_threshold') else settings.SCALPING_CONFIDENCE_THRESHOLD,
            "volume": scalping_bot_instance.volume if hasattr(scalping_bot_instance, 'volume') else settings.SCALPING_VOLUME,
        }
    else:
        config = {
            "symbol": settings.SCALPING_SYMBOL,
            "timeframe": settings.SCALPING_TIMEFRAME,
            "confidence_threshold": settings.SCALPING_CONFIDENCE_THRESHOLD,
            "volume": settings.SCALPING_VOLUME,
        }

    return jsonify(config), 200
