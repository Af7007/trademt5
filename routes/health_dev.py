from flask import Blueprint, jsonify
from flasgger import swag_from

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
@swag_from({
    'tags': ['Health'],
    'responses': {
        200: {
            'description': 'Health check successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'mt5_connected': {'type': 'boolean'},
                    'mt5_initialized': {'type': 'boolean'},
                    'mode': {'type': 'string'}
                }
            }
        }
    }
})
def health_check():
    """
    Health Check Endpoint
    ---
    description: Check the health status of the application (DEV MODE - no MT5)
    responses:
      200:
        description: Health check successful
    """
    return jsonify({
        "status": "healthy",
        "mode": "development",
        "mt5_connected": False,
        "mt5_initialized": False,
        "message": "Running in development mode without MetaTrader5"
    }), 200
