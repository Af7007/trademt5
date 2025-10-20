"""
Bot de Trading Automático MLP
Executa trades automaticamente baseado em configuração de confiança
"""

import threading
import time
from datetime import datetime, timedelta
import requests
from .mlp_storage import json_storage
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
        self.django_base_url = "http://localhost:5001"  # Django web dashboards

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
        """Executa trade REAL via MetaTrader5"""
        try:
            import MetaTrader5 as mt5

            config = json_storage.get_bot_config()
            take_profit = config.get('take_profit', 0.50)
            signal = analysis_result['signal']
            confidence = analysis_result['confidence']

            # Primeiro tenta conectar com MT5
            try:
                # Tenta inicializar MT5 com timeout e diagnóstico
                logger.info("Tentando conectar ao MT5...")
                if not mt5.initialize():
                    error_code, error_msg = mt5.last_error()
                    logger.error(f"MT5 não conectado - Error {error_code}: {error_msg}")
                    logger.error("Certifique-se que:")
                    logger.error("  1. O MetaTrader 5 está instalado")
                    logger.error("  2. O terminal MT5 está aberto")
                    logger.error("  3. Não há outra aplicação usando MT5")
                    return False
                logger.info("MT5 conectado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao conectar MT5: {e}")
                return False

            # Executa trade REAL no MT5
            symbol = 'BTCUSDc'

            # Verifica se símbolo é válido
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Símbolo {symbol} não disponível no MT5")
                return False

            # Obtém informações atuais
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error("Não foi possível obter informações do símbolo")
                return False

            # Define volume baseado nas informações do símbolo
            symbol_info_tick = mt5.symbol_info_tick(symbol)
            if symbol_info_tick is None:
                logger.error("Não foi possível obter tick do símbolo")
                return False

            # Verifica volume mínimo permitido
            min_volume = symbol_info.volume_min if hasattr(symbol_info, 'volume_min') else 0.01
            volume = max(0.01, min_volume)  # Usa pelo menos 0.01 ou volume mínimo

            # Validação de spread
            spread = symbol_info_tick.ask - symbol_info_tick.bid
            if take_profit <= spread:
                logger.warning(f"Take profit ({take_profit}) é menor que o spread ({spread:.5f})")

            # Define preço de entrada e TP/SL
            if signal == 'BUY':
                price = symbol_info_tick.ask
                sl_price = price - take_profit * 2  # Stop loss 2x mais largo
                tp_price = price + take_profit
            elif signal == 'SELL':
                price = symbol_info_tick.bid
                sl_price = price + take_profit * 2
                tp_price = price - take_profit
            else:
                logger.error("Sinal inválido para execução")
                return False

            # Cria requisição de trade
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": 240919,  # Número mágico do sistema MLP
                "comment": "MLP AUTO TRADE",
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            # Envia trade para MT5
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                ticket = result.order
                logger.info("TRADE EXECUTADO NO MT5 COM SUCESSO!")
                logger.info(f"   Ticket MT5: {ticket}")
                logger.info(f"   Sinal: {signal}")
                logger.info(f"   Preço Entrada: ${price:.2f}")
                logger.info(f"   TP: ${tp_price:.2f}")
                logger.info(f"   SL: ${sl_price:.2f}")
                logger.info(f"   Confiança: {confidence:.1%}")
                logger.info(f"   Volume: {volume} lots")

                # Salva trade no histórico MLP
                json_storage.save_trade({
                    'symbol': symbol,
                    'type': signal,
                    'analysis_id': analysis_result['analysis_id'],
                    'confidence': confidence,
                    'entry_price': price,
                    'take_profit': tp_price,
                    'stop_loss': sl_price,
                    'volume': volume,
                    'status': 'EXECUTED_MT5',
                    'mt5_ticket': ticket,
                    'executed_at': datetime.now().isoformat()
                })

                return True

            else:
                logger.error(f"MT5 Trade falhou: {result.retcode}")
                logger.error(f"Detalhes: {result.comment if hasattr(result, 'comment') else 'N/A'}")
                logger.error(f"Request: {request}")
                logger.error("Possíveis causas:")
                logger.error("- Volume muito pequeno (mínimo 0.01)")
                logger.error("- Stop Loss/TP fora do spread permitido")
                logger.error("- Saldo insuficiente")
                logger.error("- Símbolo não disponível para trading")
                return False

        except Exception as e:
            logger.error(f"Erro ao executar trade MT5: {e}")
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
