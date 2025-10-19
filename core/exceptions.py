"""
Custom exceptions for the application
"""


class MT5Exception(Exception):
    """Base exception for MT5 related errors"""

    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class MT5ConnectionError(MT5Exception):
    """Exception raised when MT5 connection fails"""
    pass


class MT5InitializationError(MT5Exception):
    """Exception raised when MT5 initialization fails"""
    pass


class MT5LoginError(MT5Exception):
    """Exception raised when MT5 login fails"""
    pass


class SymbolNotFoundError(MT5Exception):
    """Exception raised when a symbol is not found"""
    pass


class InvalidOrderError(MT5Exception):
    """Exception raised when an order is invalid"""
    pass


class OrderExecutionError(MT5Exception):
    """Exception raised when order execution fails"""
    pass


class PositionNotFoundError(MT5Exception):
    """Exception raised when a position is not found"""
    pass


class InsufficientFundsError(MT5Exception):
    """Exception raised when there are insufficient funds"""
    pass


class ValidationError(Exception):
    """Exception raised when validation fails"""

    def __init__(self, message: str, errors: dict = None):
        self.message = message
        self.errors = errors or {}
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Exception raised when authentication fails"""
    pass


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded"""
    pass
