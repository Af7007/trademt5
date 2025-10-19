"""
CORS middleware configuration
"""
from flask import Flask
from flask_cors import CORS
from core.config import settings


def setup_cors(app: Flask) -> None:
    """
    Configure CORS for the Flask application

    Args:
        app: Flask application instance
    """
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": settings.CORS_ORIGINS,
                "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],
                "expose_headers": ["Content-Range", "X-Total-Count"],
                "supports_credentials": True,
                "max_age": 3600
            },
            r"/ws/*": {
                "origins": settings.CORS_ORIGINS,
                "supports_credentials": True
            }
        }
    )
