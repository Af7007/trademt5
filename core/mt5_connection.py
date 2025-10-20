"""
MetaTrader5 connection manager (Singleton pattern)
"""
import logging
import MetaTrader5 as mt5
from typing import Optional
from .config import settings
from .exceptions import MT5ConnectionError, MT5InitializationError, MT5LoginError

logger = logging.getLogger(__name__)


class MT5Connection:
    """Singleton class for managing MT5 connection"""

    _instance: Optional['MT5Connection'] = None
    _initialized: bool = False
    _logged_in: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MT5Connection, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> bool:
        """
        Initialize MT5 connection (connect to running MT5 terminal)

        Returns:
            bool: True if successful

        Raises:
            MT5InitializationError: If initialization fails
        """
        if self._initialized:
            logger.info("MT5 already initialized")
            return True

        try:
            if not mt5.initialize():
                error_code, error_msg = mt5.last_error()
                raise MT5InitializationError(
                    f"MT5 initialization failed: {error_msg} (Certifique-se que MT5 está aberto)",
                    code=error_code
                )

            self._initialized = True
            logger.info("MT5 initialized successfully - conectado ao terminal em execução")

            # Verificar se há uma conta logada
            account_info = mt5.account_info()
            if account_info is not None:
                self._logged_in = True
                logger.info(f"MT5 conta detectada: {account_info.login} @ {account_info.server}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize MT5: {e}")
            raise MT5InitializationError(str(e))

    def login(self, login: int, password: str, server: str) -> bool:
        """
        Login to MT5 account

        Args:
            login: Account number
            password: Account password
            server: Server name

        Returns:
            bool: True if successful

        Raises:
            MT5LoginError: If login fails
        """
        if not self._initialized:
            self.initialize()

        try:
            if not mt5.login(login=login, password=password, server=server):
                error_code, error_msg = mt5.last_error()
                raise MT5LoginError(
                    f"MT5 login failed: {error_msg}",
                    code=error_code
                )

            self._logged_in = True
            logger.info(f"MT5 login successful for account {login}")
            return True

        except Exception as e:
            logger.error(f"Failed to login to MT5: {e}")
            raise MT5LoginError(str(e))

    def shutdown(self) -> None:
        """Shutdown MT5 connection"""
        if self._initialized:
            mt5.shutdown()
            self._initialized = False
            self._logged_in = False
            logger.info("MT5 connection closed")

    @property
    def is_initialized(self) -> bool:
        """Check if MT5 is initialized"""
        return self._initialized

    @property
    def is_logged_in(self) -> bool:
        """Check if logged in to MT5 account"""
        return self._logged_in

    def ensure_connection(self) -> None:
        """
        Ensure MT5 is connected, initialize if not

        Raises:
            MT5ConnectionError: If connection cannot be established
        """
        if not self._initialized:
            try:
                self.initialize()
            except Exception as e:
                raise MT5ConnectionError(f"Cannot establish MT5 connection: {e}")

    def get_version(self) -> Optional[tuple]:
        """Get MT5 terminal version"""
        if not self._initialized:
            return None
        return mt5.version()

    def get_terminal_info(self) -> Optional[dict]:
        """Get MT5 terminal information"""
        if not self._initialized:
            return None

        info = mt5.terminal_info()
        if info is None:
            return None

        return info._asdict()

    def get_account_info(self) -> Optional[dict]:
        """Get MT5 account information"""
        if not self._initialized or not self._logged_in:
            return None

        info = mt5.account_info()
        if info is None:
            return None

        return info._asdict()


# Global instance
mt5_connection = MT5Connection()
