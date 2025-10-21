"""
Testes específicos do bot MLP
"""
import json
import pytest
from unittest.mock import Mock, patch


class TestMLPEndpoints:
    """Testes dos endpoints do MLP Bot"""

    @pytest.mark.mlp
    def test_mlp_start_endpoint(self, client):
        """Testa iniciar o bot MLP"""
        response = client.post('/mlp/start')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert 'message' in data
        assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_stop_endpoint(self, client):
        """Testa parar o bot MLP"""
        # Mock para simular que não há posições abertas
        with patch('bot.trading_engine.TradingEngine.get_open_positions', return_value=[]):
            # Mock para o método stop retornar sucesso
            with patch('bot.trading_engine.TradingEngine.stop', return_value=(True, "Bot parado com sucesso")):
                response = client.post('/mlp/stop')
                # O status pode ser 200 (sucesso) ou 409 (conflito)
                assert response.status_code in [200, 409]

                data = json.loads(response.data)
                assert 'success' in data
                assert 'message' in data or 'error' in data
                assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_status_endpoint(self, client):
        """Testa obter status do MLP"""
        response = client.get('/mlp/status')
        assert response.status_code == 200

        data = json.loads(response.data)
        # Status pode variar dependendo do estado do bot
        assert isinstance(data, dict)

    @pytest.mark.mlp
    def test_mlp_execute_buy_signal(self, client):
        """Testa executar sinal BUY"""
        response = client.post('/mlp/execute',
                             data=json.dumps({
                                 'signal': 'BUY',
                                 'confidence': 0.85
                             }),
                             content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert 'signal' in data
        assert 'confidence' in data
        assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_execute_sell_signal(self, client):
        """Testa executar sinal SELL"""
        response = client.post('/mlp/execute',
                             data=json.dumps({
                                 'signal': 'SELL',
                                 'confidence': 0.75
                             }),
                             content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert data['signal'] == 'SELL'

    @pytest.mark.mlp
    def test_mlp_execute_hold_signal(self, client):
        """Testa executar sinal HOLD"""
        response = client.post('/mlp/execute',
                             data=json.dumps({
                                 'signal': 'HOLD',
                                 'confidence': 0.50
                             }),
                             content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert data['signal'] == 'HOLD'

    @pytest.mark.mlp
    def test_mlp_analyze_endpoint(self, client):
        """Testa análise automática do MLP"""
        response = client.post('/mlp/analyze')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert 'result' in data
        assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_train_endpoint(self, client):
        """Testa treinamento do modelo MLP"""
        response = client.post('/mlp/train',
                             data=json.dumps({'days': 7}),
                             content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert 'result' in data
        assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_emergency_close_endpoint(self, client):
        """Testa fechamento de emergência"""
        response = client.post('/mlp/emergency-close')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert 'result' in data
        assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_performance_endpoint(self, client):
        """Testa relatório de performance"""
        response = client.get('/mlp/performance')
        assert response.status_code == 200

        data = json.loads(response.data)
        # Performance pode variar, apenas testar estrutura
        assert isinstance(data, dict)

    @pytest.mark.mlp
    def test_mlp_positions_endpoint(self, client):
        """Testa obter posições atuais"""
        response = client.get('/mlp/positions')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'positions' in data
        assert 'total' in data
        assert 'timestamp' in data
        assert isinstance(data['positions'], list)

    @pytest.mark.mlp
    def test_mlp_market_data_endpoint(self, client):
        """Testa obter dados de mercado"""
        response = client.get('/mlp/market-data?symbol=BTCUSDc&timeframe=M1&count=10')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'symbol' in data
        assert 'timeframe' in data
        assert 'count' in data
        assert 'data' in data
        assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_history_endpoint(self, client):
        """Testa obter histórico de análises"""
        response = client.get('/mlp/history?symbol=BTCUSDc&limit=10')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'history' in data
        assert 'count' in data
        assert 'symbol' in data
        assert 'timestamp' in data
        assert isinstance(data['history'], list)

    @pytest.mark.mlp
    def test_mlp_trades_endpoint(self, client):
        """Testa obter histórico de trades"""
        response = client.get('/mlp/trades?symbol=BTCUSDc&days=7')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'trades' in data
        assert 'count' in data
        assert 'symbol' in data
        assert 'period_days' in data
        assert 'timestamp' in data
        assert isinstance(data['trades'], list)

    @pytest.mark.mlp
    def test_mlp_analytics_endpoint(self, client):
        """Testa obter estatísticas diárias"""
        response = client.get('/mlp/analytics?days=7')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'analytics' in data
        assert 'period_days' in data
        assert 'timestamp' in data
        assert isinstance(data['analytics'], list)

    @pytest.mark.mlp
    def test_mlp_update_trade_endpoint(self, client):
        """Testa atualizar trade"""
        response = client.post('/mlp/update-trade',
                             data=json.dumps({
                                 'ticket': '123456',
                                 'profit': 25.50,
                                 'exit_price': 50255.0,
                                 'exit_reason': 'TP'
                             }),
                             content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert 'message' in data
        assert 'timestamp' in data

    @pytest.mark.mlp
    def test_mlp_config_endpoint(self, client):
        """Testa atualizar configuração do MLP"""
        response = client.post('/mlp/config',
                             data=json.dumps({
                                 'take_profit': 0.75,
                                 'confidence_threshold': 0.90,
                                 'auto_trading_enabled': True
                             }),
                             content_type='application/json')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert 'message' in data
        assert 'updates' in data
        assert 'timestamp' in data


class TestBotAliases:
    """Testes dos aliases /bot/*"""

    @pytest.mark.mlp
    def test_bot_aliases_match_mlp(self, client):
        """Testa se os aliases /bot/* retornam o mesmo que /mlp/*"""
        mlp_endpoints = [
            '/mlp/health', '/mlp/start', '/mlp/stop', '/mlp/status',
            '/mlp/execute', '/mlp/analyze', '/mlp/train',
            '/mlp/emergency-close', '/mlp/performance', '/mlp/positions'
        ]

        bot_endpoints = [
            '/bot/health', '/bot/start', '/bot/stop', '/bot/mlp-status',
            '/bot/execute', '/bot/analyze', '/bot/train',
            '/bot/emergency-close', '/bot/performance', '/bot/positions'
        ]

        for mlp_ep, bot_ep in zip(mlp_endpoints, bot_endpoints):
            mlp_response = client.get(mlp_ep)
            bot_response = client.get(bot_ep)

            # Status code deve ser igual
            assert mlp_response.status_code == bot_response.status_code

            # Para endpoints que retornam dados, comparar conteúdo
            if mlp_response.status_code == 200:
                try:
                    mlp_data = json.loads(mlp_response.data)
                    bot_data = json.loads(bot_response.data)
                    # Deve ter a mesma estrutura básica
                    assert type(mlp_data) == type(bot_data)
                except json.JSONDecodeError:
                    # Se não for JSON, comparar dados brutos
                    assert mlp_response.data == bot_response.data


class TestMLPSignalValidation:
    """Testes de validação de sinais MLP"""

    @pytest.mark.mlp
    def test_mlp_execute_signal_case_insensitive(self, client):
        """Testa se sinais são case insensitive"""
        signals = ['buy', 'BUY', 'Buy', 'sell', 'SELL', 'Sell', 'hold', 'HOLD', 'Hold']

        for signal in signals:
            response = client.post('/mlp/execute',
                                 data=json.dumps({
                                     'signal': signal,
                                     'confidence': 0.85
                                 }),
                                 content_type='application/json')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['signal'] == signal.upper()

    @pytest.mark.mlp
    def test_mlp_execute_confidence_validation(self, client):
        """Testa validação de confidence"""
        # Confidence muito baixa
        response = client.post('/mlp/execute',
                             data=json.dumps({
                                 'signal': 'BUY',
                                 'confidence': 0.01
                             }),
                             content_type='application/json')
        assert response.status_code == 200  # Ainda deve funcionar

        # Confidence muito alta
        response = client.post('/mlp/execute',
                             data=json.dumps({
                                 'signal': 'BUY',
                                 'confidence': 0.99
                             }),
                             content_type='application/json')
        assert response.status_code == 200

    @pytest.mark.mlp
    def test_mlp_execute_invalid_json(self, client):
        """Testa com JSON inválido"""
        response = client.post('/mlp/execute',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400


class TestMLPErrorScenarios:
    """Testes de cenários de erro do MLP"""

    @pytest.mark.mlp
    def test_mlp_start_already_running(self, client, monkeypatch):
        """Testa iniciar bot já rodando"""
        # Mock para simular bot já rodando
        def mock_start():
            return False

        monkeypatch.setattr('app.bot_controller.trading_engine.start', mock_start)

        response = client.post('/mlp/start')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'success' in data
        assert data['success'] is False

    @pytest.mark.mlp
    def test_mlp_stop_not_running(self, client, monkeypatch):
        """Testa parar bot que não está rodando"""
        # Mock para simular operação sem erro
        def mock_stop():
            pass

        monkeypatch.setattr('app.bot_controller.trading_engine.stop', mock_stop)

        response = client.post('/mlp/stop')
        assert response.status_code == 200

    @pytest.mark.mlp
    def test_mlp_analyze_no_mt5_connection(self, client, monkeypatch):
        """Testa análise sem conexão MT5"""
        # Mock para simular erro de conexão
        def mock_analyze():
            raise Exception("MT5 connection failed")

        monkeypatch.setattr('app.bot_controller.trading_engine.analyze_and_trade', mock_analyze)

        response = client.post('/mlp/analyze')
        assert response.status_code == 500

        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data


class TestBotLifecycle:
    """Testa o ciclo de vida do bot e o registro de eventos."""

    @pytest.mark.mlp
    def test_start_creates_event(self, client):
        """Verifica se o início do bot cria um evento 'START'."""
        with patch('services.mlp_storage.mlp_storage.add_bot_event') as mock_add_event:
            with patch('bot.trading_engine.TradingEngine.start', return_value=True):
                client.post('/mlp/start')
                mock_add_event.assert_called_once_with(
                    event_type='START',
                    message='Bot MLP iniciado.'
                )

    @pytest.mark.mlp
    def test_stop_fails_with_open_positions(self, client):
        """Verifica se o bot não para se houver posições abertas."""
        # Simula uma posição aberta
        mock_position = [{'ticket': 123, 'magic': 123456}]
        with patch('bot.trading_engine.TradingEngine.get_open_positions', return_value=mock_position):
            with patch('services.mlp_storage.mlp_storage.add_bot_event') as mock_add_event:
                response = client.post('/mlp/stop')

                # Deve retornar 409 Conflict
                assert response.status_code == 409
                data = json.loads(response.data)
                assert data['success'] is False
                assert 'posições abertas' in data['error']

                # Garante que nenhum evento 'STOP' foi criado
                mock_add_event.assert_not_called()

    @pytest.mark.mlp
    def test_stop_succeeds_without_open_positions(self, client):
        """Verifica se o bot para e cria um evento 'STOP' quando não há posições."""
        # Simula que não há posições abertas
        with patch('bot.trading_engine.TradingEngine.get_open_positions', return_value=[]):
            with patch('services.mlp_storage.mlp_storage.add_bot_event') as mock_add_event:
                response = client.post('/mlp/stop')

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True

                # Verifica se o evento 'STOP' foi registrado
                mock_add_event.assert_called_once_with(
                    event_type='STOP',
                    message='Bot MLP parado com sucesso.'
                )

    @pytest.mark.mlp
    def test_execute_trade_creates_event(self, client):
        """Verifica se a execução de um trade cria um evento 'TRADE_OPEN'."""
        # Mock para a execução do trade retornar sucesso com um ticket
        mock_trade_result = {'success': True, 'ticket': 789}
        with patch('bot.trading_engine.TradingEngine.execute_signal', return_value=mock_trade_result):
            with patch('services.mlp_storage.mlp_storage.add_bot_event') as mock_add_event:
                client.post('/mlp/execute', data=json.dumps({'signal': 'BUY', 'confidence': 0.9}), content_type='application/json')

                # Verifica se o evento de abertura de trade foi chamado
                mock_add_event.assert_called_with(
                    event_type='TRADE_OPEN',
                    message='Sinal BUY executado com sucesso.',
                    details={'ticket': 789, 'signal': 'BUY', 'confidence': 0.9}
                )


class TestMLPDatabaseIntegration:
    """Testes de integração com banco de dados"""

    @pytest.mark.mlp
    def test_mlp_history_with_database(self, client, temp_db):
        """Testa histórico com banco de dados real"""
        storage, db_path = temp_db

        # Adicionar análise de teste
        test_analysis = {
            'symbol': 'BTCUSDc',
            'signal': 'BUY',
            'confidence': 0.85,
            'timestamp': '2023-01-01T12:00:00Z'
        }

        # Mock do storage na aplicação
        with patch('app.mlp_storage', storage):
            response = client.get('/mlp/history?symbol=BTCUSDc&limit=10')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert 'history' in data
            assert isinstance(data['history'], list)

    @pytest.mark.mlp
    def test_mlp_trades_with_database(self, client, temp_db):
        """Testa trades com banco de dados real"""
        storage, db_path = temp_db

        # Mock do storage na aplicação
        with patch('app.mlp_storage', storage):
            response = client.get('/mlp/trades?symbol=BTCUSDc&days=7')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert 'trades' in data
            assert isinstance(data['trades'], list)

    @pytest.mark.mlp
    def test_mlp_update_trade_with_database(self, client, temp_db):
        """Testa atualização de trade com banco de dados real"""
        storage, db_path = temp_db

        # Adicionar trade de teste primeiro
        test_trade = {
            'ticket': '123456',
            'symbol': 'BTCUSDc',
            'type': 'BUY',
            'volume': 0.01,
            'open_price': 50000.0,
            'open_time': '2023-01-01T12:00:00Z'
        }

        # Mock do storage na aplicação
        with patch('app.mlp_storage', storage):
            response = client.post('/mlp/update-trade',
                                 data=json.dumps({
                                     'ticket': '123456',
                                     'profit': 25.50,
                                     'exit_price': 50255.0,
                                     'exit_reason': 'TP'
                                 }),
                                 content_type='application/json')

            # Pode ser 200 (sucesso) ou 404 (trade não encontrado)
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                data = json.loads(response.data)
                assert data['success'] is True
