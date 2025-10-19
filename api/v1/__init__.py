"""
API v1 routes
"""
from flask import Blueprint

from .routes.market import market_bp
from .routes.trading import trading_bp
from .routes.account import account_bp
from .routes.strategies import strategies_bp
from .routes.auth import auth_bp

# Create main v1 blueprint
v1_bp = Blueprint('v1', __name__)

# Register sub-blueprints
v1_bp.register_blueprint(market_bp, url_prefix='/market')
v1_bp.register_blueprint(trading_bp, url_prefix='/trading')
v1_bp.register_blueprint(account_bp, url_prefix='/account')
v1_bp.register_blueprint(strategies_bp, url_prefix='/strategies')
v1_bp.register_blueprint(auth_bp, url_prefix='/auth')

__all__ = ['v1_bp']
