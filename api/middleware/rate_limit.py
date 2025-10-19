"""
Rate limiting middleware
"""
import logging
import time
from functools import wraps
from flask import request, jsonify
from typing import Dict, Tuple, Callable
from collections import defaultdict

from core.config import settings
from core.exceptions import RateLimitError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.limit = settings.RATE_LIMIT_PER_MINUTE

    def get_client_id(self) -> str:
        """
        Get unique identifier for the client

        Returns:
            Client identifier (IP address or user)
        """
        # Use authenticated user if available
        if hasattr(request, 'user') and request.user:
            return f"user:{request.user}"

        # Otherwise use IP address
        return f"ip:{request.remote_addr}"

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Check if request is allowed based on rate limit

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        if not self.enabled:
            return True, self.limit

        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        # Check limit
        request_count = len(self.requests[client_id])
        if request_count >= self.limit:
            return False, 0

        # Add current request
        self.requests[client_id].append(current_time)

        remaining = self.limit - (request_count + 1)
        return True, remaining

    def cleanup_old_entries(self):
        """Remove expired entries to prevent memory leak"""
        current_time = time.time()
        window_start = current_time - 60

        # Remove clients with no recent requests
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > window_start
            ]
            if not self.requests[client_id]:
                del self.requests[client_id]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(f: Callable) -> Callable:
    """
    Decorator to apply rate limiting to routes

    Args:
        f: Function to wrap

    Returns:
        Wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not rate_limiter.enabled:
            return f(*args, **kwargs)

        client_id = rate_limiter.get_client_id()
        is_allowed, remaining = rate_limiter.is_allowed(client_id)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return jsonify({
                "error": "Rate limit exceeded",
                "message": f"Maximum {rate_limiter.limit} requests per minute"
            }), 429

        # Add rate limit headers
        response = f(*args, **kwargs)

        # If response is a tuple (response, status_code)
        if isinstance(response, tuple):
            resp_obj, status_code = response[0], response[1]
        else:
            resp_obj, status_code = response, 200

        # Add headers if response is a Flask Response object
        if hasattr(resp_obj, 'headers'):
            resp_obj.headers['X-RateLimit-Limit'] = str(rate_limiter.limit)
            resp_obj.headers['X-RateLimit-Remaining'] = str(remaining)

        if isinstance(response, tuple):
            return resp_obj, status_code
        return resp_obj

    return decorated_function
