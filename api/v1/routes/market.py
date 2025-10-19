"""
Market data routes
"""
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from api.middleware.auth import optional_auth
from api.middleware.rate_limit import rate_limit
from services.market_service import market_service
from models.requests import CandlesRequest

market_bp = Blueprint('market', __name__)


@market_bp.route('/symbols', methods=['GET'])
@optional_auth
@rate_limit
@swag_from({
    'tags': ['Market'],
    'summary': 'Get all available symbols',
    'description': 'Retrieve list of all trading symbols available on MT5',
    'responses': {
        200: {
            'description': 'List of symbols',
            'schema': {
                'type': 'object',
                'properties': {
                    'symbols': {
                        'type': 'array',
                        'items': {'type': 'object'}
                    },
                    'count': {'type': 'integer'}
                }
            }
        }
    }
})
def get_symbols():
    """Get all available symbols"""
    symbols = market_service.get_symbols()
    return jsonify({
        "symbols": symbols,
        "count": len(symbols)
    }), 200


@market_bp.route('/symbols/<symbol>', methods=['GET'])
@optional_auth
@rate_limit
@swag_from({
    'tags': ['Market'],
    'summary': 'Get symbol information',
    'description': 'Retrieve detailed information about a specific symbol',
    'parameters': [{
        'name': 'symbol',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': 'Symbol name (e.g., BTCUSDc)'
    }],
    'responses': {
        200: {'description': 'Symbol information'},
        404: {'description': 'Symbol not found'}
    }
})
def get_symbol_info(symbol: str):
    """Get detailed symbol information"""
    info = market_service.get_symbol_info(symbol)
    return jsonify(info), 200


@market_bp.route('/symbols/search', methods=['GET'])
@optional_auth
@rate_limit
@swag_from({
    'tags': ['Market'],
    'summary': 'Search symbols',
    'description': 'Search for symbols by name or description',
    'parameters': [{
        'name': 'q',
        'in': 'query',
        'type': 'string',
        'required': True,
        'description': 'Search query'
    }],
    'responses': {
        200: {'description': 'Matching symbols'},
        400: {'description': 'Invalid request'}
    }
})
def search_symbols():
    """Search symbols"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    results = market_service.search_symbols(query)
    return jsonify({
        "results": results,
        "count": len(results)
    }), 200


@market_bp.route('/ticks/<symbol>', methods=['GET'])
@optional_auth
@rate_limit
@swag_from({
    'tags': ['Market'],
    'summary': 'Get latest tick',
    'description': 'Retrieve the latest tick/quote for a symbol',
    'parameters': [{
        'name': 'symbol',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': 'Symbol name'
    }],
    'responses': {
        200: {'description': 'Tick information'},
        404: {'description': 'Symbol not found'}
    }
})
def get_tick(symbol: str):
    """Get latest tick for symbol"""
    tick = market_service.get_tick(symbol)
    return jsonify(tick), 200


@market_bp.route('/candles/<symbol>', methods=['GET'])
@optional_auth
@rate_limit
@swag_from({
    'tags': ['Market'],
    'summary': 'Get candle data',
    'description': 'Retrieve OHLCV candle data for a symbol',
    'parameters': [
        {
            'name': 'symbol',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Symbol name'
        },
        {
            'name': 'timeframe',
            'in': 'query',
            'type': 'string',
            'required': False,
            'default': 'M1',
            'description': 'Timeframe (M1, M5, M15, M30, H1, H4, D1, W1, MN1)'
        },
        {
            'name': 'count',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'default': 100,
            'description': 'Number of candles to fetch'
        }
    ],
    'responses': {
        200: {'description': 'Candle data'},
        400: {'description': 'Invalid parameters'},
        404: {'description': 'Symbol not found or no data'}
    }
})
def get_candles(symbol: str):
    """Get candle data for symbol"""
    timeframe = request.args.get('timeframe', 'M1')
    count = int(request.args.get('count', 100))

    candles = market_service.get_candles(
        symbol=symbol,
        timeframe=timeframe,
        count=count
    )

    return jsonify({
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "count": len(candles)
    }), 200
