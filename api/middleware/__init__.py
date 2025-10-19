"""
Middleware for the API
"""
from .cors import setup_cors
from .auth import auth_required, optional_auth
from .error_handler import setup_error_handlers
from .rate_limit import RateLimiter

__all__ = ["setup_cors", "auth_required", "optional_auth", "setup_error_handlers", "RateLimiter"]
