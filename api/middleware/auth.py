"""
Authentication middleware
"""
import logging
from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta
from typing import Optional, Callable

from core.config import settings
from core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


def create_access_token(username: str) -> dict:
    """
    Create JWT access token

    Args:
        username: Username to encode in token

    Returns:
        Dictionary with token and expiration
    """
    expiration = datetime.utcnow() + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": username,
        "exp": expiration,
        "iat": datetime.utcnow()
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid token")
        return None


def verify_api_key(api_key: str) -> bool:
    """
    Verify API key

    Args:
        api_key: API key to verify

    Returns:
        True if valid
    """
    if not settings.API_KEY:
        # If no API key is configured, accept any key
        return True

    return api_key == settings.API_KEY


def get_token_from_request() -> Optional[str]:
    """
    Extract token from request headers

    Returns:
        Token string or None
    """
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]

    # Check X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key

    return None


def auth_required(f: Callable) -> Callable:
    """
    Decorator to require authentication for routes

    Args:
        f: Function to wrap

    Returns:
        Wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        # Try JWT verification first
        payload = verify_token(token)
        if payload:
            request.user = payload.get("sub")
            return f(*args, **kwargs)

        # Try API key verification
        if verify_api_key(token):
            request.user = "api_key_user"
            return f(*args, **kwargs)

        return jsonify({"error": "Invalid authentication credentials"}), 401

    return decorated_function


def optional_auth(f: Callable) -> Callable:
    """
    Decorator for optional authentication (sets user if authenticated)

    Args:
        f: Function to wrap

    Returns:
        Wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()

        if token:
            # Try JWT verification
            payload = verify_token(token)
            if payload:
                request.user = payload.get("sub")
            # Try API key verification
            elif verify_api_key(token):
                request.user = "api_key_user"
            else:
                request.user = None
        else:
            request.user = None

        return f(*args, **kwargs)

    return decorated_function
