"""
Authentication routes
"""
from flask import Blueprint, request, jsonify
from flasgger import swag_from

from api.middleware.auth import create_access_token
from models.requests import LoginRequest
from models.responses import TokenResponse, ErrorResponse

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Login and get access token',
    'description': 'Authenticate and receive a JWT access token',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'password': {'type': 'string'}
            },
            'required': ['username', 'password']
        }
    }],
    'responses': {
        200: {
            'description': 'Login successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'token_type': {'type': 'string'},
                    'expires_in': {'type': 'integer'}
                }
            }
        },
        401: {'description': 'Invalid credentials'}
    }
})
def login():
    """
    Login endpoint

    Simple authentication - in production, verify against a user database
    """
    try:
        data = request.get_json()

        # Validate request
        login_req = LoginRequest(**data)

        # TODO: Implement real authentication against user database
        # For now, accept any non-empty credentials
        if login_req.username and login_req.password:
            token_data = create_access_token(login_req.username)
            return jsonify(token_data), 200

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route('/verify', methods=['GET'])
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Verify token validity',
    'description': 'Check if the provided token is valid',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True,
        'description': 'Bearer token'
    }],
    'responses': {
        200: {'description': 'Token is valid'},
        401: {'description': 'Token is invalid or expired'}
    }
})
def verify():
    """
    Verify token endpoint
    """
    from api.middleware.auth import verify_token, get_token_from_request

    token = get_token_from_request()
    if not token:
        return jsonify({"error": "No token provided"}), 401

    payload = verify_token(token)
    if payload:
        return jsonify({
            "valid": True,
            "user": payload.get("sub"),
            "expires": payload.get("exp")
        }), 200

    return jsonify({"valid": False, "error": "Invalid or expired token"}), 401
