"""
Account information routes
"""
from flask import Blueprint, jsonify
from flasgger import swag_from

from api.middleware.auth import auth_required
from api.middleware.rate_limit import rate_limit
from services.trading_service import trading_service
from core.mt5_connection import mt5_connection

account_bp = Blueprint('account', __name__)


@account_bp.route('/info', methods=['GET'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Account'],
    'summary': 'Get account information',
    'description': 'Retrieve detailed information about the trading account',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True,
        'description': 'Bearer token'
    }],
    'responses': {
        200: {
            'description': 'Account information',
            'schema': {
                'type': 'object',
                'properties': {
                    'login': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'server': {'type': 'string'},
                    'currency': {'type': 'string'},
                    'balance': {'type': 'number'},
                    'equity': {'type': 'number'},
                    'profit': {'type': 'number'},
                    'margin': {'type': 'number'},
                    'margin_free': {'type': 'number'},
                    'margin_level': {'type': 'number'},
                    'leverage': {'type': 'integer'}
                }
            }
        },
        401: {'description': 'Unauthorized'},
        503: {'description': 'MT5 connection error'}
    }
})
def get_account_info():
    """Get account information"""
    info = trading_service.get_account_info()
    return jsonify(info), 200


@account_bp.route('/balance', methods=['GET'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Account'],
    'summary': 'Get account balance summary',
    'description': 'Get simplified balance and equity information',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {
            'description': 'Balance information',
            'schema': {
                'type': 'object',
                'properties': {
                    'balance': {'type': 'number'},
                    'equity': {'type': 'number'},
                    'profit': {'type': 'number'},
                    'margin': {'type': 'number'},
                    'margin_free': {'type': 'number'},
                    'margin_level': {'type': 'number'}
                }
            }
        },
        401: {'description': 'Unauthorized'}
    }
})
def get_balance():
    """Get account balance summary"""
    info = trading_service.get_account_info()

    balance_info = {
        "balance": info.get("balance", 0),
        "equity": info.get("equity", 0),
        "profit": info.get("profit", 0),
        "margin": info.get("margin", 0),
        "margin_free": info.get("margin_free", 0),
        "margin_level": info.get("margin_level", 0),
        "currency": info.get("currency", "USD")
    }

    return jsonify(balance_info), 200


@account_bp.route('/status', methods=['GET'])
@auth_required
@rate_limit
@swag_from({
    'tags': ['Account'],
    'summary': 'Get account trading status',
    'description': 'Check if trading is allowed and other status information',
    'parameters': [{
        'name': 'Authorization',
        'in': 'header',
        'type': 'string',
        'required': True
    }],
    'responses': {
        200: {
            'description': 'Account status',
            'schema': {
                'type': 'object',
                'properties': {
                    'trade_allowed': {'type': 'boolean'},
                    'trade_expert': {'type': 'boolean'},
                    'connected': {'type': 'boolean'},
                    'logged_in': {'type': 'boolean'}
                }
            }
        },
        401: {'description': 'Unauthorized'}
    }
})
def get_account_status():
    """Get account trading status"""
    info = trading_service.get_account_info()

    status = {
        "trade_allowed": info.get("trade_allowed", False),
        "trade_expert": info.get("trade_expert", False),
        "connected": mt5_connection.is_initialized,
        "logged_in": mt5_connection.is_logged_in,
        "login": info.get("login"),
        "server": info.get("server")
    }

    return jsonify(status), 200
