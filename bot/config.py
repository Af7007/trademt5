"""
Configuração do Bot de Trading MT5 com MLP
"""
import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TradingConfig:
    """Configurações de Trading"""
    symbol: str = "BTCUSDc"  # Símbolo correto disponível na conta
    lot_size: float = 0.01
    max_positions: int = 1
    stop_loss_pips: int = 100
    take_profit_pips: int = 200
    magic_number: int = 123456

    # Novas configurações específicas para o teste
    target_profit_usd: float = 0.50  # Lucro alvo de $0.50
    risk_percentage: float = 0.01  # 1% de risco por operação
    dynamic_lot_size: bool = False  # DESABILITADO: usar lote fixo
    single_operation_mode: bool = True  # Uma operação somente
    wait_for_position_close: bool = True  # Aguardar fechamento da posição


@dataclass
class MLPConfig:
    """Configurações do Modelo MLP"""
    hidden_layers: List[int] = None
    learning_rate: float = 0.001
    epochs: int = 100
    batch_size: int = 32
    sequence_length: int = 60  # Número de candles para análise
    features: List[str] = None

    def __post_init__(self):
        if self.hidden_layers is None:
            self.hidden_layers = [128, 64, 32]
        if self.features is None:
            self.features = [
                'open', 'high', 'low', 'close', 'volume',
                'rsi', 'macd', 'bb_upper', 'bb_lower', 'sma_20', 'sma_50'
            ]


@dataclass
class MT5Config:
    """Configurações de Conexão MT5"""
    mt5_path: str = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
    expert_path: str = None
    login: int = None
    password: str = None
    server: str = None

    def __post_init__(self):
        if self.expert_path is None:
            self.expert_path = os.path.join(os.path.dirname(self.mt5_path), "MQL5", "Experts")


@dataclass
class BotConfig:
    """Configuração Principal do Bot"""
    trading: TradingConfig = None
    mlp: MLPConfig = None
    mt5: MT5Config = None
    log_level: str = "INFO"
    log_file: str = "bot/logs/trading_bot.log"
    api_port: int = 5002
    model_save_path: str = "bot/models/"

    def __post_init__(self):
        if self.trading is None:
            self.trading = TradingConfig()
        if self.mlp is None:
            self.mlp = MLPConfig()
        if self.mt5 is None:
            self.mt5 = MT5Config()


# Configuração padrão
DEFAULT_CONFIG = BotConfig()


def load_config_from_env() -> BotConfig:
    """Carrega configuração a partir de variáveis de ambiente"""
    config = BotConfig()

    # Trading config
    if os.getenv('MT5_SYMBOL'):
        config.trading.symbol = os.getenv('MT5_SYMBOL')
    if os.getenv('MT5_LOT_SIZE'):
        config.trading.lot_size = float(os.getenv('MT5_LOT_SIZE'))
    if os.getenv('MT5_STOP_LOSS'):
        config.trading.stop_loss_pips = int(os.getenv('MT5_STOP_LOSS'))
    if os.getenv('MT5_TAKE_PROFIT'):
        config.trading.take_profit_pips = int(os.getenv('MT5_TAKE_PROFIT'))

    # MT5 config
    if os.getenv('MT5_PATH'):
        config.mt5.mt5_path = os.getenv('MT5_PATH')
    if os.getenv('MT5_LOGIN'):
        config.mt5.login = int(os.getenv('MT5_LOGIN'))
    if os.getenv('MT5_PASSWORD'):
        config.mt5.password = os.getenv('MT5_PASSWORD')
    if os.getenv('MT5_SERVER'):
        config.mt5.server = os.getenv('MT5_SERVER')

    # MLP config
    if os.getenv('MLP_LEARNING_RATE'):
        config.mlp.learning_rate = float(os.getenv('MLP_LEARNING_RATE'))
    if os.getenv('MLP_EPOCHS'):
        config.mlp.epochs = int(os.getenv('MLP_EPOCHS'))

    return config


def get_config() -> BotConfig:
    """Retorna configuração carregada"""
    return load_config_from_env() if os.getenv('USE_ENV_CONFIG') else DEFAULT_CONFIG
