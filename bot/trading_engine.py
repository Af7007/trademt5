"""
Motor de execução de operações do bot MLP-MT5
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import threading
import pandas as pd

from .config import get_config
from .mlp_model import MLPModel
from .mt5_connector import MT5Connector, Position


class TradingEngine:
    """Motor principal do bot de trading"""

    def __init__(self):
        self.config = get_config()
        self.mlp_model = MLPModel()
        self.mt5_connector = MT5Connector()
        self.is_running = False
        self.last_prediction = None
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'start_time': None
        }

        # Configurar logging
        self.logger = logging.getLogger(__name__)

        # Thread para monitoramento
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()

    def start(self) -> bool:
        """Inicia o bot de trading"""
        try:
            self.logger.info("Iniciando Trading Bot...")

            # Conectar ao MT5
            if not self.mt5_connector.connect():
                self.logger.error("Falha na conexão com MT5")
                return False

            # Carregar modelo treinado
            self.mlp_model.load_model()

            # Inicializar métricas
            self.performance_metrics['start_time'] = datetime.now()

            # Iniciar monitoramento
            self.is_running = True
            self.stop_monitoring.clear()
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            self.logger.info("Trading Bot iniciado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao iniciar bot: {str(e)}")
            return False

    def stop(self):
        """Para o bot de trading"""
        try:
            self.logger.info("Parando Trading Bot...")

            # Parar monitoramento
            self.is_running = False
            self.stop_monitoring.set()

            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)

            # Desconectar MT5
            self.mt5_connector.disconnect()

            self.logger.info("Trading Bot parado")
        except Exception as e:
            self.logger.error(f"Erro ao parar bot: {str(e)}")

    def execute_signal(self, signal: str, confidence: float = 0.5) -> Dict[str, Any]:
        """Executa operação baseada no sinal do modelo"""
        try:
            if not self.is_running:
                return {'success': False, 'error': 'Bot não está rodando'}

            if confidence < 0.6:  # Threshold mínimo de confiança
                self.logger.info(f"Confiança baixa ({confidence:.2f}), ignorando sinal: {signal}")
                return {'success': False, 'error': 'Confiança baixa'}

            # Verificar posições existentes
            positions = self.mt5_connector.get_positions()
            if len(positions) >= self.config.trading.max_positions:
                self.logger.info(f"Máximo de posições atingido ({len(positions)})")
                return {'success': False, 'error': 'Máximo de posições atingido'}

            # Obter preço atual
            symbol_info = self.mt5_connector.get_symbol_info()
            if symbol_info is None:
                return {'success': False, 'error': 'Não foi possível obter informações do símbolo'}

            current_price = symbol_info['ask'] if signal == 'BUY' else symbol_info['bid']

            # Calcular SL e TP
            sl, tp = self.mt5_connector.calculate_sl_tp(
                self.config.trading.symbol, signal, current_price
            )

            # Enviar ordem
            ticket = self.mt5_connector.send_market_order(
                symbol=self.config.trading.symbol,
                order_type=signal,
                volume=self.config.trading.lot_size,
                sl=sl,
                tp=tp
            )

            if ticket:
                # Atualizar métricas
                self.performance_metrics['total_trades'] += 1
                self.last_prediction = {
                    'signal': signal,
                    'confidence': confidence,
                    'ticket': ticket,
                    'timestamp': datetime.now()
                }

                self.logger.info(f"Operação executada: {signal} (Ticket: {ticket}, Confiança: {confidence:.2f})")
                return {
                    'success': True,
                    'signal': signal,
                    'ticket': ticket,
                    'confidence': confidence,
                    'price': current_price,
                    'sl': sl,
                    'tp': tp
                }
            else:
                return {'success': False, 'error': 'Falha ao enviar ordem'}

        except Exception as e:
            self.logger.error(f"Erro ao executar sinal: {str(e)}")
            return {'success': False, 'error': str(e)}

    def analyze_and_trade(self) -> Dict[str, Any]:
        """Analisa mercado e executa operação se necessário"""
        try:
            if not self.is_running:
                return {'success': False, 'error': 'Bot não está rodando'}

            # Obter dados de mercado
            market_data = self.mt5_connector.get_market_data(
                symbol=self.config.trading.symbol,
                timeframe='M1',
                count=self.config.mlp.sequence_length
            )

            if len(market_data) < 30:  # Mínimo de dados necessários
                return {'success': False, 'error': 'Dados insuficientes para análise'}

            # Fazer predição
            signal, confidence = self.mlp_model.predict(market_data)

            self.logger.info(f"Análise: {signal} (Confiança: {confidence:.2f})")

            # Executar se sinal for BUY ou SELL
            if signal in ['BUY', 'SELL']:
                return self.execute_signal(signal, confidence)
            else:
                return {
                    'success': True,
                    'signal': 'HOLD',
                    'confidence': confidence,
                    'message': 'Sinal HOLD - nenhuma operação executada'
                }

        except Exception as e:
            self.logger.error(f"Erro na análise e trading: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Obtém status atual do bot"""
        try:
            positions = self.mt5_connector.get_positions()
            account_info = self.mt5_connector.get_account_info()

            return {
                'is_running': self.is_running,
                'mt5_connected': self.mt5_connector.is_connected(),
                'positions_count': len(positions),
                'positions': [
                    {
                        'ticket': pos.ticket,
                        'type': pos.type,
                        'volume': pos.volume,
                        'profit': pos.profit,
                        'symbol': pos.symbol
                    } for pos in positions
                ],
                'account_info': account_info,
                'last_prediction': self.last_prediction,
                'performance': self.performance_metrics,
                'uptime': str(datetime.now() - self.performance_metrics['start_time']) if self.performance_metrics['start_time'] else None
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter status: {str(e)}")
            return {'error': str(e)}

    def train_model(self, days: int = 30) -> Dict[str, Any]:
        """Treina o modelo com dados históricos"""
        try:
            self.logger.info(f"Iniciando treinamento com {days} dias de dados...")

            # Obter dados históricos
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Coletar dados de diferentes timeframes
            all_data = []
            for tf in ['M1', 'M5', 'M15']:
                data = self.mt5_connector.get_market_data(
                    symbol=self.config.trading.symbol,
                    timeframe=tf,
                    count=min(days * 24 * 60 // int(tf[1:]), 10000)  # Ajustar count baseado no timeframe
                )
                if len(data) > 0:
                    all_data.append(data)

            if not all_data:
                return {'success': False, 'error': 'Não foi possível obter dados históricos'}

            # Usar dados M1 para treinamento
            training_data = all_data[0] if all_data else pd.DataFrame()

            if len(training_data) < 100:
                return {'success': False, 'error': 'Dados insuficientes para treinamento'}

            # Gerar labels
            labels = self.mlp_model.generate_training_labels(training_data)

            # Treinar modelo
            results = self.mlp_model.train(training_data, labels)

            # Salvar modelo
            self.mlp_model.save_model()

            self.logger.info("Treinamento concluído com sucesso")
            return {
                'success': True,
                'results': results,
                'data_points': len(training_data),
                'training_time': results.get('epochs_trained', 0)
            }

        except Exception as e:
            self.logger.error(f"Erro no treinamento: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        self.logger.info("Iniciando loop de monitoramento...")

        while not self.stop_monitoring.is_set():
            try:
                # Análise e trading a cada minuto
                self.analyze_and_trade()

                # Aguardar próximo ciclo
                time.sleep(60)  # 1 minuto

            except Exception as e:
                self.logger.error(f"Erro no loop de monitoramento: {str(e)}")
                time.sleep(30)  # Aguardar 30 segundos em caso de erro

        self.logger.info("Loop de monitoramento finalizado")

    def emergency_close_all(self) -> Dict[str, Any]:
        """Fecha todas as posições em caso de emergência"""
        try:
            positions = self.mt5_connector.get_positions()
            closed_positions = []

            for position in positions:
                success = self.mt5_connector.close_position(position.ticket)
                if success:
                    closed_positions.append(position.ticket)

            return {
                'success': True,
                'closed_positions': closed_positions,
                'total_closed': len(closed_positions)
            }

        except Exception as e:
            self.logger.error(f"Erro ao fechar posições de emergência: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_performance_report(self) -> Dict[str, Any]:
        """Gera relatório de performance"""
        try:
            positions = self.mt5_connector.get_positions()
            account_info = self.mt5_connector.get_account_info()

            # Calcular métricas
            total_positions = len(positions)
            total_profit = sum(pos.profit for pos in positions)

            # Win rate
            winning_positions = len([pos for pos in positions if pos.profit > 0])
            win_rate = (winning_positions / total_positions * 100) if total_positions > 0 else 0

            # Drawdown (simplificado)
            current_equity = account_info.get('equity', 0) if account_info else 0
            initial_balance = account_info.get('balance', 0) if account_info else 0
            current_drawdown = ((initial_balance - current_equity) / initial_balance * 100) if initial_balance > 0 else 0

            return {
                'summary': {
                    'total_positions': total_positions,
                    'winning_positions': winning_positions,
                    'losing_positions': total_positions - winning_positions,
                    'win_rate': round(win_rate, 2),
                    'total_profit': round(total_profit, 2),
                    'current_drawdown': round(current_drawdown, 2)
                },
                'positions': [
                    {
                        'ticket': pos.ticket,
                        'type': pos.type,
                        'profit': round(pos.profit, 2),
                        'volume': pos.volume,
                        'open_time': pos.open_time.isoformat()
                    } for pos in positions
                ],
                'account': account_info,
                'bot_metrics': self.performance_metrics
            }

        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {str(e)}")
            return {'error': str(e)}
