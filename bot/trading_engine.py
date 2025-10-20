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

# Import absoluto para evitar problemas com execução direta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.mt5_connection import mt5_connection, MT5ConnectionError

# Django setup for MLP storage - REMOVED
# Agora usa apenas JSON storage
django_storage_available = False


class TradingEngine:
    """Motor principal do bot de trading"""

    def __init__(self):
        self.config = get_config()
        self.mlp_model = MLPModel()
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

            # Conectar ao MT5 usando mt5_connection
            mt5_connection.ensure_connection()

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

            # Desconectar MT5 usando mt5_connection
            mt5_connection.shutdown()

            self.logger.info("Trading Bot parado")
        except Exception as e:
            self.logger.error(f"Erro ao parar bot: {str(e)}")

    def execute_signal(self, signal: str, confidence: float = 0.5, analysis_id: int = None) -> Dict[str, Any]:
        """Executa operação baseada no sinal do modelo"""
        try:
            if not self.is_running:
                return {'success': False, 'error': 'Bot não está rodando'}

            if confidence < 0.6:  # Threshold mínimo de confiança
                self.logger.info(f"Confiança baixa ({confidence:.2f}), ignorando sinal: {signal}")
                return {'success': False, 'error': 'Confiança baixa'}

            # Verificar posições existentes usando mt5_connection
            # Nota: mt5_connection não tem método get_positions, precisamos usar MT5 diretamente
            positions = mt5.positions_get()
            if positions is not None and len(positions) >= self.config.trading.max_positions:
                self.logger.info(f"Máximo de posições atingido ({len(positions)})")
                return {'success': False, 'error': 'Máximo de posições atingido'}

            # Obter preço atual usando mt5_connection
            symbol_info = mt5_connection.get_terminal_info()
            if symbol_info is None:
                return {'success': False, 'error': 'Não foi possível obter informações do terminal'}

            # Para obter preços atuais, precisamos usar MT5 diretamente
            import MetaTrader5 as mt5
            symbol_data = mt5.symbol_info(self.config.trading.symbol)
            if symbol_data is None:
                return {'success': False, 'error': 'Não foi possível obter informações do símbolo'}

            current_price = symbol_data.ask if signal == 'BUY' else symbol_data.bid

            # Calcular SL e TP baseado na configuração
            point = symbol_data.point
            sl_pips = self.config.trading.stop_loss_pips
            tp_pips = self.config.trading.take_profit_pips

            if signal.upper() == 'BUY':
                sl = current_price - (sl_pips * point * 10)  # Convert pips to price
                tp = current_price + (tp_pips * point * 10)
            else:  # SELL
                sl = current_price + (sl_pips * point * 10)
                tp = current_price - (tp_pips * point * 10)

            sl = round(sl, symbol_data.digits)
            tp = round(tp, symbol_data.digits)

            # Enviar ordem usando MT5 diretamente
            order_type = mt5.ORDER_TYPE_BUY if signal.upper() == 'BUY' else mt5.ORDER_TYPE_SELL

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.config.trading.symbol,
                "volume": self.config.trading.lot_size,
                "type": order_type,
                "magic": self.config.trading.magic_number,
                "comment": "MLP Bot Order"
            }

            # Adicionar SL e TP se especificados
            if sl > 0:
                request["sl"] = sl
            if tp > 0:
                request["tp"] = tp

            # Enviar ordem
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Erro ao enviar ordem: {result.retcode} - {result.comment}")
                return {'success': False, 'error': f'Falha ao enviar ordem: {result.comment}'}

            ticket = result.order

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
                    'tp': tp,
                    'analysis_id': analysis_id
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

            # Obter dados de mercado usando MT5 diretamente
            import MetaTrader5 as mt5

            # Converter timeframe para MT5
            tf_dict = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }

            timeframe_mt5 = tf_dict.get('M1', mt5.TIMEFRAME_M1)

            # Obter dados
            rates = mt5.copy_rates_from_pos(self.config.trading.symbol, timeframe_mt5, 0, self.config.mlp.sequence_length)

            if rates is None or len(rates) == 0:
                self.logger.error(f"Não foi possível obter dados para {self.config.trading.symbol}")
                return {'success': False, 'error': 'Dados insuficientes para análise'}

            # Converter para DataFrame
            market_data = pd.DataFrame(rates)
            market_data['time'] = pd.to_datetime(market_data['time'], unit='s')
            market_data = market_data[['time', 'open', 'high', 'low', 'close', 'tick_volume']]

            if len(market_data) < 30:  # Mínimo de dados necessários
                return {'success': False, 'error': 'Dados insuficientes para análise'}

            # Calcular indicadores técnicos
            indicators = {
                'rsi': self._calculate_rsi(market_data['close'], 14).iloc[-1] if len(market_data) > 14 else None,
                'macd_signal': self._calculate_macd_signal(market_data['close']).iloc[-1] if len(market_data) > 26 else None,
                'bb_upper': self._calculate_bollinger_bands(market_data['close'], 20)[0].iloc[-1] if len(market_data) > 20 else None,
                'bb_lower': self._calculate_bollinger_bands(market_data['close'], 20)[1].iloc[-1] if len(market_data) > 20 else None,
                'sma_20': market_data['close'].rolling(window=20).mean().iloc[-1] if len(market_data) >= 20 else None,
                'sma_50': market_data['close'].rolling(window=50).mean().iloc[-1] if len(market_data) >= 50 else None,
            }

            # Fazer predição
            signal, confidence = self.mlp_model.predict(market_data)

            self.logger.info(f"Análise: {signal} (Confiança: {confidence:.2f})")

            # Preparar dados para salvar no Django
            analysis_data = {
                'symbol': self.config.trading.symbol,
                'signal': signal,
                'confidence': confidence,
                'indicators': indicators,
                'market_data': {
                    'open': market_data['open'].iloc[-1],
                    'high': market_data['high'].iloc[-1],
                    'low': market_data['low'].iloc[-1],
                    'close': market_data['close'].iloc[-1],
                    'volume': market_data['tick_volume'].iloc[-1],
                },
                'technical_signals': {
                    'rsi_divergence': self._detect_rsi_divergence(market_data),
                    'volume_spike': self._detect_volume_spike(market_data),
                    'trend_strength': self._calculate_trend_strength(market_data),
                    'support_resistance': self._detect_support_resistance(market_data),
                },
                'market_conditions': {
                    'volatility': self._calculate_volatility(market_data),
                    'trend': self._detect_trend(market_data),
                    'volume': self._calculate_volume_profile(market_data),
                }
            }

            # Analysis saved using JSON storage instead of Django

            # Executar se sinal for BUY ou SELL
            if signal in ['BUY', 'SELL']:
                result = self.execute_signal(signal, confidence, None)
                return result
            else:
                result = {
                    'success': True,
                    'signal': 'HOLD',
                    'confidence': confidence,
                    'message': 'Sinal HOLD - nenhuma operação executada'
                }
                return result

        except Exception as e:
            self.logger.error(f"Erro na análise e trading: {str(e)}")
            return {'success': False, 'error': str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Obtém status atual do bot"""
        try:
            # Obter posições usando MT5 diretamente
            import MetaTrader5 as mt5
            positions_mt5 = mt5.positions_get()

            positions = []
            if positions_mt5:
                for pos in positions_mt5:
                    if pos.magic == self.config.trading.magic_number:
                        position = {
                            'ticket': pos.ticket,
                            'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                            'volume': pos.volume,
                            'profit': pos.profit,
                            'symbol': pos.symbol
                        }
                        positions.append(position)

            # Obter informações da conta usando mt5_connection
            account_info = mt5_connection.get_account_info()

            return {
                'is_running': self.is_running,
                'mt5_connected': mt5_connection.is_initialized,
                'positions_count': len(positions),
                'positions': positions,
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

            # Coletar dados de diferentes timeframes usando MT5 diretamente
            import MetaTrader5 as mt5

            all_data = []
            tf_dict = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15
            }

            for tf_name, tf_mt5 in tf_dict.items():
                # Calcular count baseado no timeframe
                count = min(days * 24 * 60 // int(tf_name[1:]), 10000)

                # Obter dados
                rates = mt5.copy_rates_from_pos(self.config.trading.symbol, tf_mt5, 0, count)

                if rates is not None and len(rates) > 0:
                    # Converter para DataFrame
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
                    all_data.append(df)

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
            import MetaTrader5 as mt5

            # Obter posições do bot (com magic number específico)
            positions_mt5 = mt5.positions_get()

            closed_positions = []
            if positions_mt5:
                for pos in positions_mt5:
                    if pos.magic == self.config.trading.magic_number:
                        # Fechar posição
                        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY

                        request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "position": pos.ticket,
                            "symbol": pos.symbol,
                            "volume": pos.volume,
                            "type": close_type,
                            "magic": self.config.trading.magic_number,
                            "comment": "Emergency Close"
                        }

                        result = mt5.order_send(request)
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            closed_positions.append(pos.ticket)

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
            import MetaTrader5 as mt5

            # Obter posições do bot usando MT5 diretamente
            positions_mt5 = mt5.positions_get()

            positions = []
            if positions_mt5:
                for pos in positions_mt5:
                    if pos.magic == self.config.trading.magic_number:
                        position = {
                            'ticket': pos.ticket,
                            'type': 'BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                            'profit': pos.profit,
                            'volume': pos.volume,
                            'open_time': datetime.fromtimestamp(pos.time)
                        }
                        positions.append(position)

            # Obter informações da conta usando mt5_connection
            account_info = mt5_connection.get_account_info()

            # Calcular métricas
            total_positions = len(positions)
            total_profit = sum(pos['profit'] for pos in positions)

            # Win rate
            winning_positions = len([pos for pos in positions if pos['profit'] > 0])
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
                        'ticket': pos['ticket'],
                        'type': pos['type'],
                        'profit': round(pos['profit'], 2),
                        'volume': pos['volume'],
                        'open_time': pos['open_time'].isoformat()
                    } for pos in positions
                ],
                'account': account_info,
                'bot_metrics': self.performance_metrics
            }

        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {str(e)}")
            return {'error': str(e)}

    # Métodos auxiliares para cálculos técnicos
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd_signal(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
        """Calculate MACD signal line"""
        fast_ema = prices.ewm(span=fast).mean()
        slow_ema = prices.ewm(span=slow).mean()
        macd = fast_ema - slow_ema
        return macd.ewm(span=signal).mean()

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> tuple:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, lower

    def _detect_rsi_divergence(self, data: pd.DataFrame) -> bool:
        """Detect RSI divergence (simplified)"""
        if len(data) < 20:
            return False
        return (data['close'].iloc[-1] < data['close'].iloc[-10] and
                self._calculate_rsi(data['close']).iloc[-1] > self._calculate_rsi(data['close']).iloc[-10])

    def _detect_volume_spike(self, data: pd.DataFrame) -> bool:
        """Detect volume spike (simplified)"""
        if len(data) < 20:
            return False
        avg_volume = data['tick_volume'].iloc[-20:-1].mean()
        return data['tick_volume'].iloc[-1] > avg_volume * 2

    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """Calculate trend strength (simplified)"""
        if len(data) < 20:
            return 0.0
        returns = data['close'].pct_change().iloc[-20:]
        return abs(returns.mean() / returns.std()) if returns.std() > 0 else 0.0

    def _detect_support_resistance(self, data: pd.DataFrame) -> dict:
        """Detect support/resistance levels (simplified)"""
        if len(data) < 20:
            return {}
        recent_high = data['high'].iloc[-20:].max()
        recent_low = data['low'].iloc[-20:].min()
        return {'support': recent_low, 'resistance': recent_high}

    def _calculate_volatility(self, data: pd.DataFrame) -> float:
        """Calculate volatility (standard deviation)"""
        if len(data) < 20:
            return 0.0
        returns = data['close'].pct_change().iloc[-20:]
        return returns.std() * 100  # Percentage

    def _detect_trend(self, data: pd.DataFrame) -> str:
        """Detect trend direction (simplified)"""
        if len(data) < 50:
            return 'SIDEWAYS'
        sma_20 = data['close'].rolling(window=20).mean()
        sma_50 = data['close'].rolling(window=50).mean()
        if sma_20.iloc[-1] > sma_50.iloc[-1]:
            return 'BULLISH'
        elif sma_20.iloc[-1] < sma_50.iloc[-1]:
            return 'BEARISH'
        else:
            return 'SIDEWAYS'

    def _calculate_volume_profile(self, data: pd.DataFrame) -> dict:
        """Calculate volume profile (simplified)"""
        if len(data) < 20:
            return {}
        avg_volume = data['tick_volume'].iloc[-20:].mean()
        current_volume = data['tick_volume'].iloc[-1]
        return {
            'average': avg_volume,
            'current': current_volume,
            'above_average': current_volume > avg_volume
        }
