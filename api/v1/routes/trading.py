"""
Trading routes - orders, positions, execution
"""
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from api.middleware.auth import auth_required
from api.middleware.rate_limit import rate_limit
from services.trading_service import trading_service
from models.requests import MarketOrderRequest, ModifyPositionRequest, ClosePositionRequest

trading_bp = Blueprint('trading', __name__)


@trading_bp.route('/orders', methods=['POST'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Trading'],
    'summary': 'Send market order',
    'description': 'Execute a market order (BUY or SELL)',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True,
        'description': 'Bearer token'
    }, {
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'symbol': {'type': 'string', 'example': 'BTCUSDc'},
                'volume': {'type': 'number', 'example': 0.01},
                'order_type': {'type': 'string', 'enum': ['BUY', 'SELL']},
                'sl': {'type': 'number', 'example': 45000.0},
                'tp': {'type': 'number', 'example': 50000.0},
                'magic': {'type': 'integer', 'example': 12345},
                'comment': {'type': 'string', 'example': 'API order'}
            },
            'required': ['symbol', 'volume', 'order_type']
        }
    }],
    'responses': {
        200: {'description': 'Order executed successfully'},
        400: {'description': 'Invalid order parameters or execution failed'},
        401: {'description': 'Unauthorized'}
    }
})
def send_order():
    """Send a market order"""
    data = request.get_json()

    # Validate request
    order_req = MarketOrderRequest(**data)

    # Execute order
    result = trading_service.send_market_order(
        symbol=order_req.symbol,
        volume=order_req.volume,
        order_type=order_req.order_type,
        sl=order_req.sl,
        tp=order_req.tp,
        deviation=order_req.deviation,
        magic=order_req.magic,
        comment=order_req.comment
    )

    return jsonify({
        "message": "Order executed successfully",
        "result": result
    }), 200


@trading_bp.route('/positions', methods=['GET'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Trading'],
    'summary': 'Get open positions',
    'description': 'Retrieve all open trading positions',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True,
            'description': 'Bearer token'
        },
        {
            'name': 'magic',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'Filter by magic number'
        }
    ],
    'responses': {
        200: {'description': 'List of open positions'},
        401: {'description': 'Unauthorized'}
    }
})
def get_positions():
    """Get all open positions"""
    magic = request.args.get('magic', type=int)

    positions = trading_service.get_positions(magic=magic)

    total_profit = sum(p.get('profit', 0) for p in positions)

    return jsonify({
        "positions": positions,
        "count": len(positions),
        "total_profit": total_profit
    }), 200


@trading_bp.route('/positions/<int:position_id>', methods=['GET'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Trading'],
    'summary': 'Get position by ID',
    'description': 'Retrieve a specific position by ticket/ID',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True
        },
        {
            'name': 'position_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'Position ticket/ID'
        }
    ],
    'responses': {
        200: {'description': 'Position details'},
        404: {'description': 'Position not found'},
        401: {'description': 'Unauthorized'}
    }
})
def get_position(position_id: int):
    """Get specific position"""
    position = trading_service.get_position_by_ticket(position_id)
    return jsonify(position), 200


@trading_bp.route('/positions/<int:position_id>', methods=['PATCH'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Trading'],
    'summary': 'Modify position SL/TP',
    'description': 'Modify Stop Loss and/or Take Profit of a position',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True
        },
        {
            'name': 'position_id',
            'in': 'path',
            'type': 'integer',
            'required': True
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'sl': {'type': 'number'},
                    'tp': {'type': 'number'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Position modified successfully'},
        400: {'description': 'Invalid parameters'},
        404: {'description': 'Position not found'},
        401: {'description': 'Unauthorized'}
    }
})
def modify_position(position_id: int):
    """Modify position SL/TP"""
    data = request.get_json()

    # Validate request
    modify_req = ModifyPositionRequest(position_id=position_id, **data)

    # Modify position
    result = trading_service.modify_position(
        position_id=modify_req.position_id,
        sl=modify_req.sl,
        tp=modify_req.tp
    )

    return jsonify({
        "message": "Position modified successfully",
        "result": result
    }), 200


@trading_bp.route('/positions/<int:position_id>', methods=['DELETE'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Trading'],
    'summary': 'Close position',
    'description': 'Close a specific position',
    'parameters': [
        {
            'name': 'Authorization',
            'in': 'header',
            'type': 'string',
            'required': True
        },
        {
            'name': 'position_id',
            'in': 'path',
            'type': 'integer',
            'required': True
        },
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'volume': {'type': 'number', 'description': 'Volume to close (omit for full close)'},
                    'deviation': {'type': 'integer', 'default': 20}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Position closed successfully'},
        400: {'description': 'Close failed'},
        404: {'description': 'Position not found'},
        401: {'description': 'Unauthorized'}
    }
})
def close_position(position_id: int):
    """Close a position"""
    data = request.get_json() or {}

    # Close position
    result = trading_service.close_position(
        position_id=position_id,
        volume=data.get('volume'),
        deviation=data.get('deviation', 20)
    )

    return jsonify({
        "message": "Position closed successfully",
        "result": result
    }), 200


@trading_bp.route('/positions/close-all', methods=['POST'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Trading'],
    'summary': 'Close all positions',
    'description': 'Close all open positions, optionally filtered by type and magic',
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
                    'order_type': {'type': 'string', 'enum': ['BUY', 'SELL', 'all'], 'default': 'all'},
                    'magic': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Positions closed'},
        401: {'description': 'Unauthorized'}
    }
})
def close_all_positions():
    """Close all positions"""
    data = request.get_json() or {}

    results = trading_service.close_all_positions(
        order_type=data.get('order_type', 'all'),
        magic=data.get('magic')
    )

    return jsonify({
        "message": f"Closed {len(results)} positions",
        "results": results,
        "count": len(results)
    }), 200


@trading_bp.route('/positions/total', methods=['GET'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Trading'],
    'summary': 'Get total positions count',
    'description': 'Get the total number of open positions',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {'description': 'Total positions count'},
        401: {'description': 'Unauthorized'}
    }
})
def get_positions_total():
    """Get total positions count"""
    total = trading_service.get_positions_total()
    return jsonify({"total": total}), 200
