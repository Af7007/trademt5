"""
Global error handler middleware
"""
import logging
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError as PydanticValidationError

from core.exceptions import (
    MT5Exception,
    MT5ConnectionError,
    MT5InitializationError,
    MT5LoginError,
    SymbolNotFoundError,
    InvalidOrderError,
    OrderExecutionError,
    PositionNotFoundError,
    InsufficientFundsError,
    ValidationError,
    AuthenticationError,
    RateLimitError
)

logger = logging.getLogger(__name__)


def setup_error_handlers(app: Flask) -> None:
    """
    Setup global error handlers for the Flask application

    Args:
        app: Flask application instance
    """

    @app.errorhandler(MT5ConnectionError)
    @app.errorhandler(MT5InitializationError)
    @app.errorhandler(MT5LoginError)
    def handle_mt5_connection_error(e):
        """Handle MT5 connection errors"""
        logger.error(f"MT5 connection error: {e}")
        return jsonify({
            "error": str(e.message),
            "code": e.code,
            "type": "MT5ConnectionError"
        }), 503

    @app.errorhandler(SymbolNotFoundError)
    def handle_symbol_not_found(e):
        """Handle symbol not found errors"""
        logger.warning(f"Symbol not found: {e}")
        return jsonify({
            "error": str(e.message),
            "code": e.code,
            "type": "SymbolNotFoundError"
        }), 404

    @app.errorhandler(InvalidOrderError)
    def handle_invalid_order(e):
        """Handle invalid order errors"""
        logger.warning(f"Invalid order: {e}")
        return jsonify({
            "error": str(e.message),
            "code": e.code,
            "type": "InvalidOrderError"
        }), 400

    @app.errorhandler(OrderExecutionError)
    def handle_order_execution_error(e):
        """Handle order execution errors"""
        logger.error(f"Order execution error: {e}")
        return jsonify({
            "error": str(e.message),
            "code": e.code,
            "type": "OrderExecutionError"
        }), 400

    @app.errorhandler(PositionNotFoundError)
    def handle_position_not_found(e):
        """Handle position not found errors"""
        logger.warning(f"Position not found: {e}")
        return jsonify({
            "error": str(e.message),
            "code": e.code,
            "type": "PositionNotFoundError"
        }), 404

    @app.errorhandler(InsufficientFundsError)
    def handle_insufficient_funds(e):
        """Handle insufficient funds errors"""
        logger.warning(f"Insufficient funds: {e}")
        return jsonify({
            "error": str(e.message),
            "code": e.code,
            "type": "InsufficientFundsError"
        }), 400

    @app.errorhandler(ValidationError)
    @app.errorhandler(PydanticValidationError)
    def handle_validation_error(e):
        """Handle validation errors"""
        logger.warning(f"Validation error: {e}")

        if isinstance(e, PydanticValidationError):
            errors = {}
            for error in e.errors():
                field = ".".join(str(x) for x in error["loc"])
                errors[field] = error["msg"]

            return jsonify({
                "error": "Validation error",
                "errors": errors,
                "type": "ValidationError"
            }), 400

        return jsonify({
            "error": str(e.message),
            "errors": e.errors,
            "type": "ValidationError"
        }), 400

    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(e):
        """Handle authentication errors"""
        logger.warning(f"Authentication error: {e}")
        return jsonify({
            "error": str(e),
            "type": "AuthenticationError"
        }), 401

    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(e):
        """Handle rate limit errors"""
        logger.warning(f"Rate limit error: {e}")
        return jsonify({
            "error": str(e),
            "type": "RateLimitError"
        }), 429

    @app.errorhandler(MT5Exception)
    def handle_mt5_exception(e):
        """Handle generic MT5 exceptions"""
        logger.error(f"MT5 exception: {e}")
        return jsonify({
            "error": str(e.message),
            "code": e.code,
            "type": "MT5Exception"
        }), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions"""
        return jsonify({
            "error": e.description,
            "type": "HTTPException"
        }), e.code

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        """Handle all other exceptions"""
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e) if app.debug else "An unexpected error occurred",
            "type": "InternalServerError"
        }), 500

    logger.info("Error handlers configured")
