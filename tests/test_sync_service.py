"""
Testes para o serviço de sincronização de trades do MT5.
"""
import json
import pytest
from unittest.mock import patch

class TestSyncServiceEndpoints:
    """Testa os endpoints da API de sincronização."""

    @pytest.mark.sync
    def test_sync_status_endpoint(self, client):
        """Testa o endpoint de status da sincronização."""
        # Usamos 'patch' para simular que o serviço está rodando
        with patch('services.sync_mt5_trades_service.mt5_trade_sync.is_running', True):
            response = client.get('/sync/status')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'is_running' in data
            assert 'sync_stats' in data
            assert data['is_running'] is True

    @pytest.mark.sync
    def test_sync_manual_sync_endpoint(self, client, mock_mt5):
        """Testa o endpoint de sincronização manual."""
        # Mock para a função que busca os trades no MT5
        with patch('services.sync_mt5_trades_service.mt5.history_deals_get') as mock_deals:
            mock_deals.return_value = []  # Simula que não há novos trades
            response = client.post('/sync/manual-sync')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'result' in data
            assert data['result']['saved_trades'] == 0

    @pytest.mark.sync
    def test_sync_stop_endpoint(self, client):
        """Testa o endpoint para parar o serviço de sincronização."""
        with patch('services.sync_mt5_trades_service.mt5_trade_sync.stop') as mock_stop:
            mock_stop.return_value = True
            response = client.post('/sync/stop')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Serviço de sincronização MT5 parado' in data['message']

    @pytest.mark.sync
    def test_sync_summary_endpoint(self, client):
        """Testa o endpoint de resumo dos trades."""
        # Mock para a função que busca o resumo no banco
        with patch('services.sync_mt5_trades_service.mt5_trade_sync.get_trade_summary') as mock_summary:
            mock_summary.return_value = {
                'total_trades': 10,
                'win_rate': 70.0,
                'total_profit': 150.50
            }
            response = client.get('/sync/summary?days=7')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'total_trades' in data
            assert data['total_trades'] == 10

    @pytest.mark.sync
    def test_start_fails_if_mt5_not_connected(self, client):
        """Testa se o serviço não inicia se o MT5 não estiver conectado."""
        from services.sync_mt5_trades_service import MT5TradeSyncService
        sync_service = MT5TradeSyncService()

        # Mock para simular falha na conexão
        with patch('services.sync_mt5_trades_service.mt5_connection.is_connected', return_value=False):
            started = sync_service.start()
            assert started is False
            assert sync_service.is_running is False

    @pytest.mark.sync
    def test_sync_now_handles_mt5_history_deals_none(self, client):
        """Testa o tratamento de erro quando history_deals_get retorna None."""
        from services.sync_mt5_trades_service import MT5TradeSyncService
        sync_service = MT5TradeSyncService()

        with patch('services.sync_mt5_trades_service.mt5_connection.is_connected', return_value=True):
            # Mock para simular retorno None do MT5
            with patch('services.sync_mt5_trades_service.mt5.history_deals_get', return_value=None):
                result = sync_service.sync_now()
                assert 'error' in result
                assert 'MT5 retornou None' in result['error']

    @pytest.mark.sync
    def test_update_config(self, client):
        """Testa a atualização da configuração do serviço."""
        from services.sync_mt5_trades_service import mt5_trade_sync
        
        original_interval = mt5_trade_sync.sync_interval
        original_lookback = mt5_trade_sync.lookback_days

        # Atualiza a configuração
        success = mt5_trade_sync.update_config(sync_interval=120, lookback_days=14)
        assert success is True
        assert mt5_trade_sync.sync_interval == 120
        assert mt5_trade_sync.lookback_days == 14

        # Restaura a configuração original para não afetar outros testes
        mt5_trade_sync.update_config(sync_interval=original_interval, lookback_days=original_lookback)

    @pytest.mark.sync
    def test_sync_summary_endpoint_error(self, client):
        """Testa o tratamento de erro no endpoint de resumo."""
        # Mock para simular uma exceção ao buscar o resumo
        with patch('services.sync_mt5_trades_service.mt5_trade_sync.get_trade_summary') as mock_summary:
            mock_summary.side_effect = Exception("Database error")
            response = client.get('/sync/summary?days=7')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert data['error'] == "Database error"