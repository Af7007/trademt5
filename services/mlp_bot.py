"""
Bot de Trading Automático MLP
Executa trades automaticamente baseado em configuração de confiança
"""

import threading
import time
from datetime import datetime, timedelta
import requests
from services.mlp_storage import json_storage
import logging

logger = logging.getLogger(__name__)

class MLPTradingBot:
    """Bot de trading automático para MLP"""

    def __init__(self):
        self.is_running = False
        self.bot_thread = None
        self.check_interval = 5  # Verificar a cada 5 segundos

        # URLs das APIs (ajuste conforme necessário)
        self.api_base_url = "http://localhost:5000"  # Flask APIs (MLP Bot)
        self.django_base_url = "http://localhost:8000"  # Django web dashboards

    def start(self):
        """Inicia o bot de trading"""
        if self.is_running:
            logger.warning("Bot já está rodando")
            return False

        # Inicia o bot via APIs
        try:
            response = requests.post(f"{self.api_base_url}/mlp/start")
            if response.status_code != 200:
                logger.error("Erro ao iniciar bot via API")
                return False
        except Exception as e:
            logger.error(f"Erro ao conectar API: {e}")
            return False

        # Atualiza configuração
        json_storage.update_bot_config(is_running=True, auto_trading_enabled=True)

        # Inicia thread do bot
        self.is_running = True
        self.bot_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.bot_thread.start()

        logger.info("MLP Trading Bot iniciado com sucesso!")
        return True

    def stop(self):
        """Para o bot de trading"""
        if not self.is_running:
            logger.warning("Bot não está rodando")
            return False

        # Para o bot via APIs
        try:
            response = requests.post(f"{self.api_base_url}/mlp/stop")
            if response.status_code != 200:
                logger.error("Erro ao parar bot via API")
                return False
        except Exception as e:
            logger.error(f"Erro ao conectar API: {e}")
            return False

        # Atualiza configuração
        self.is_running = False
        json_storage.update_bot_config(is_running=False, auto_trading_enabled=False)

        # Espera thread terminar
        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=10)

        logger.info("MLP Trading Bot parado com sucesso!")
        return True

    def _trading_loop(self):
        """Loop principal de trading"""
        logger.info("Iniciando loop de trading automático")

        while self.is_running:
            try:
                # Verifica configuração atual
                config = json_storage.get_bot_config()

                if not config.get('auto_trading_enabled', False):
                    logger.info("Bot habilitado mas não em modo automático")
                    time.sleep(self.check_interval)
                    continue

                # Verifica se pode executar trade (intervalo entre operações)
                if not json_storage.can_execute_trade():
                    logger.debug("Aguardando intervalo entre operações")
                    time.sleep(self.check_interval)
                    continue

                # Executa análise MLP
                analysis_result = self._execute_analysis()

                if analysis_result and self._should_trade(analysis_result):
                    # Executa trade
                    self._execute_trade(analysis_result)
                    json_storage.update_last_operation_time()
                    logger.info("Trade executado - aguardando próximo ciclo")

                # Intervalo entre verificações
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Erro no loop de trading: {e}")
                time.sleep(self.check_interval * 2)  # Aguardar mais em caso de erro

        logger.info("Loop de trading finalizado")

    def _execute_analysis(self):
        """Executa análise via API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/mlp/analyze",
                json={'symbol': 'BTCUSDc', 'auto_execute': False},
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success', False):
                    confidence = float(result.get('confidence', 0))
                    signal = result.get('signal', 'HOLD')

                    logger.info(f"Analise: {signal} {confidence:.1%} confiança")

                    # Salva análise no histórico
                    json_storage.save_analysis({
                        'symbol': result.get('symbol', 'BTCUSDc'),
                        'signal': signal,
                        'confidence': confidence,
                        'indicators': result.get('indicators', {}),
                        'timestamp': result.get('timestamp'),
                        'mt5_connected': result.get('mt5_connected', False),
                        'price_data': result.get('price_data', {})
                    })

                    return {
                        'signal': signal,
                        'confidence': confidence,
                        'analysis_id': result.get('analysis_id'),
                        'price_data': result.get('price_data', {})
                    }

            return None

        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return None

    def _should_trade(self, analysis_result):
        """Verifica se deve executar trade baseado na configuração"""
        config = json_storage.get_bot_config()

        # Verificar confiança mínima
        min_confidence = config.get('confidence_threshold', 0.85)
        current_confidence = analysis_result.get('confidence', 0)

        if current_confidence < min_confidence:
            logger.info(f"Confiança baixa: {current_confidence:.1%} < {min_confidence:.1%} (mínimo)")
            return False

        # Só executar BUY/SELL, não HOLD
        signal = analysis_result.get('signal', 'HOLD')
        if signal not in ['BUY', 'SELL']:
            logger.info(f"Sinal HOLD - aguardando oportunidade")
            return False

        logger.info(f"Critérios atendidos: {signal} {current_confidence:.1%}")
        return True

    def _execute_trade(self, analysis_result):
        """Executa trade via API"""
        try:
            config = json_storage.get_bot_config()
            take_profit = config.get('take_profit', 0.50)

            trade_payload = {
                'symbol': 'BTCUSDc',
                'signal': analysis_result['signal'],
                'analysis_id': analysis_result['analysis_id']
            }

            # Adicionar TP se disponível
            price_data = analysis_result.get('price_data', {})
            if price_data and 'close' in price_data:
                current_price = price_data['close']

                if analysis_result['signal'] == 'BUY':
                    tp_price = current_price + take_profit
                elif analysis_result['signal'] == 'SELL':
                    tp_price = current_price - take_profit

                trade_payload['take_profit'] = tp_price
                logger.info(f"TP configurado: ${tp_price:.2f} (atual: ${current_price:.2f})")

            # Executa trade
            response = requests.post(
                f"{self.api_base_url}/mlp/execute",
                json=trade_payload,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('success', False):
                    logger.info(f"Trade executado com sucesso!")
                    logger.info(f"   Sinal: {analysis_result['signal']}")
                    logger.info(f"   TP: ${take_profit:.2f}")
                    logger.info(f"   Confiança: {analysis_result['confidence']:.1%}")

                    # Salva trade no histórico
                    json_storage.save_trade({
                        'symbol': 'BTCUSDc',
                        'type': analysis_result['signal'],
                        'analysis_id': analysis_result['analysis_id'],
                        'confidence': analysis_result['confidence'],
                        'entry_price': price_data.get('close'),
                        'take_profit': take_profit,
                        'expected_tp_price': trade_payload.get('take_profit'),
                        'status': 'OPEN',
                        'ticket': result.get('trade', {}).get('ticket', 'UNKNOWN')
                    })

                    return True
                else:
                    logger.error(f"Erro na execução: {result.get('error', 'Desconhecido')}")
                    return False
            else:
                logger.error(f"HTTP Error {response.status_code} na execução")
                return False

        except Exception as e:
            logger.error(f"Erro ao executar trade: {e}")
            return False

    def get_status(self):
        """Retorna status do bot"""
        config = json_storage.get_bot_config()

        return {
            'is_running': self.is_running,
            'config': config,
            'last_operation': config.get('last_operation_time'),
            'can_trade_now': json_storage.can_execute_trade()
        }


# Instância global do bot
mlp_bot = MLPTradingBot()
