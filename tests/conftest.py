"""
Configuração compartilhada para todos os testes
"""
import os
import sys
import pytest
from unittest.mock import Mock, MagicMock
import tempfile
import shutil

# Adicionar o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services.mlp_storage import MLPStorage


@pytest.fixture
def client():
    """Cliente de teste Flask"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_mt5():
    """Mock do MetaTrader5 para testes"""
    mock = Mock()
    mock.TIMEFRAME_M1 = 1
    mock.TIMEFRAME_M5 = 5
    mock.TIMEFRAME_M15 = 15
    mock.TIMEFRAME_H1 = 16385
    mock.TIMEFRAME_H4 = 16388
    mock.TIMEFRAME_D1 = 16408

    # Mock de funções principais
    mock.initialize.return_value = True
    mock.login.return_value = True
    mock.account_info.return_value = Mock(balance=10000.0, equity=10000.0, profit=0.0)
    mock.positions_get.return_value = []
    mock.orders_get.return_value = []
    mock.symbol_info_tick.return_value = Mock(
        bid=50000.0, ask=50001.0, last=50000.5, volume=100
    )
    mock.copy_rates_from_pos.return_value = [
        (1640995200, 50000.0, 50100.0, 49900.0, 50050.0, 1000, 0, 0),
        (1640995260, 50050.0, 50150.0, 49950.0, 50100.0, 1100, 0, 0),
    ]

    return mock


@pytest.fixture
def temp_db():
    """Banco de dados temporário para testes"""
    # Criar diretório temporário
    temp_dir = tempfile.mkdtemp()

    # Configurar caminho do banco para o temporário
    db_path = os.path.join(temp_dir, 'test_mlp_data.db')

    # Substituir o caminho padrão
    original_path = os.path.join(os.path.dirname(__file__), '..', 'mlp_data.db')
    if os.path.exists(original_path):
        os.rename(original_path, original_path + '.backup')

    # Criar banco temporário
    storage = MLPStorage(db_path=db_path)
    storage.init_db()

    yield storage, db_path

    # Cleanup
    if os.path.exists(original_path + '.backup'):
        if os.path.exists(original_path):
            os.remove(original_path)
        os.rename(original_path + '.backup', original_path)

    # Remover temporário
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_market_data():
    """Dados de mercado de exemplo para testes"""
    return {
        'symbol': 'BTCUSDc',
        'bid': 50000.0,
        'ask': 50001.0,
        'spread': 1.0,
        'rsi': 55.2,
        'sma_20': 49800.0,
        'sma_50': 49500.0,
        'volume': 1000,
        'timestamp': '2023-01-01T12:00:00Z'
    }


@pytest.fixture
def sample_mlp_analysis():
    """Análise MLP de exemplo para testes"""
    return {
        'symbol': 'BTCUSDc',
        'signal': 'BUY',
        'confidence': 0.85,
        'rsi': 55.2,
        'sma_20': 49800.0,
        'sma_50': 49500.0,
        'volume': 1000,
        'price': 50000.0,
        'indicators': {
            'rsi': 55.2,
            'macd': (0.1, 0.05, 0.05),
            'bb_upper': 50200.0,
            'bb_lower': 49800.0
        },
        'timestamp': '2023-01-01T12:00:00Z'
    }


@pytest.fixture
def sample_trade():
    """Trade de exemplo para testes"""
    return {
        'ticket': '123456',
        'symbol': 'BTCUSDc',
        'type': 'BUY',
        'volume': 0.01,
        'open_price': 50000.0,
        'open_time': '2023-01-01T12:00:00Z',
        'profit': 25.50,
        'commission': -0.50,
        'swap': 0.0,
        'close_time': '2023-01-01T13:00:00Z',
        'close_price': 50255.0,
        'exit_reason': 'TP'
    }


@pytest.fixture(autouse=True)
def mock_environment():
    """Configurar variáveis de ambiente para testes"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['MT5_API_PORT'] = '5000'
    os.environ['MT5_DEMO'] = 'true'

    yield

    # Cleanup
    if 'FLASK_ENV' in os.environ:
        del os.environ['FLASK_ENV']
    if 'MT5_API_PORT' in os.environ:
        del os.environ['MT5_API_PORT']
    if 'MT5_DEMO' in os.environ:
        del os.environ['MT5_DEMO']
