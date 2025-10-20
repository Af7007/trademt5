"""
API Controller para controle remoto do bot MLP-MT5
"""
from flask import Blueprint, request, jsonify
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
import threading

from .config import get_config
from .trading_engine import TradingEngine


class BotAPIController:
    """Controlador da API para o bot de trading"""

    def __init__(self):
        self.config = get_config()
        self.trading_engine = TradingEngine()

        # Criar blueprint ao invés de aplicativo Flask
        self.app = Blueprint('bot_mlp_api', __name__)

        # Configurar logging
        self.logger = logging.getLogger(__name__)

        # Configurar rotas
        self._setup_routes()

    def _setup_routes(self):
        """Configura as rotas da API"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Verifica saúde da API"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'bot_running': self.trading_engine.is_running,
                'mt5_connected': self.trading_engine.get_status().get('mt5_connected', False)
            })

        @self.app.route('/start', methods=['POST'])
        def start_bot():
            """Inicia o bot de trading"""
            try:
                success = self.trading_engine.start()
                return jsonify({
                    'success': success,
                    'message': 'Bot iniciado com sucesso' if success else 'Falha ao iniciar bot',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Erro ao iniciar bot: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/stop', methods=['POST'])
        def stop_bot():
            """Para o bot de trading"""
            try:
                self.trading_engine.stop()
                return jsonify({
                    'success': True,
                    'message': 'Bot parado com sucesso',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Erro ao parar bot: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/mlp-status', methods=['GET'])
        def get_bot_status():
            """Obtém status atual do bot"""
            try:
                status = self.trading_engine.get_status()
                return jsonify(status)
            except Exception as e:
                self.logger.error(f"Erro ao obter status: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/execute', methods=['POST'])
        def execute_signal():
            """Executa sinal de trading"""
            try:
                # Tentar obter JSON de diferentes formas
                data = None
                try:
                    data = request.get_json(force=True)
                except:
                    data = request.get_json(silent=True)

                # Se ainda não conseguiu, tentar parsing manual
                if data is None:
                    import json
                    try:
                        data = json.loads(request.data)
                    except:
                        data = {}

                if not data or 'signal' not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Campo "signal" é obrigatório (BUY, SELL, HOLD)',
                        'timestamp': datetime.now().isoformat()
                    }), 400

                signal = str(data['signal']).upper()
                confidence = float(data.get('confidence', 0.5))

                if signal not in ['BUY', 'SELL', 'HOLD']:
                    return jsonify({
                        'success': False,
                        'error': 'Signal deve ser BUY, SELL ou HOLD',
                        'timestamp': datetime.now().isoformat()
                    }), 400

                # Executar apenas se for BUY ou SELL
                if signal in ['BUY', 'SELL']:
                    result = self.trading_engine.execute_signal(signal, confidence)
                else:
                    result = {
                        'success': True,
                        'signal': 'HOLD',
                        'message': 'Sinal HOLD recebido - nenhuma operação executada'
                    }

                return jsonify({
                    'success': result.get('success', True),
                    'signal': signal,
                    'confidence': confidence,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                self.logger.error(f"Erro ao executar sinal: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/analyze', methods=['POST'])
        def analyze_and_execute():
            """Analisa mercado e executa operação automaticamente"""
            try:
                result = self.trading_engine.analyze_and_trade()
                return jsonify({
                    'success': result.get('success', False),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Erro na análise: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/train', methods=['POST'])
        def train_model():
            """Treina o modelo com dados históricos"""
            try:
                data = request.get_json()
                days = data.get('days', 30) if data else 30

                result = self.trading_engine.train_model(days)
                return jsonify({
                    'success': result.get('success', False),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Erro no treinamento: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/emergency-close', methods=['POST'])
        def emergency_close():
            """Fecha todas as posições em emergência"""
            try:
                result = self.trading_engine.emergency_close_all()
                return jsonify({
                    'success': result.get('success', False),
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Erro no fechamento de emergência: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/performance', methods=['GET'])
        def get_performance():
            """Obtém relatório de performance"""
            try:
                report = self.trading_engine.get_performance_report()
                return jsonify(report)
            except Exception as e:
                self.logger.error(f"Erro ao obter performance: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/positions', methods=['GET'])
        def get_positions():
            """Obtém posições atuais"""
            try:
                # Obter posições usando o método atualizado do TradingEngine
                status = self.trading_engine.get_status()
                positions = status.get('positions', [])

                return jsonify({
                    'positions': positions,
                    'total': len(positions),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Erro ao obter posições: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

        @self.app.route('/bot/market-data', methods=['GET'])
        def get_market_data():
            """Obtém dados de mercado"""
            try:
                import MetaTrader5 as mt5

                symbol = request.args.get('symbol', self.config.trading.symbol)
                timeframe = request.args.get('timeframe', 'M1')
                count = int(request.args.get('count', 100))

                # Converter timeframe para MT5
                tf_dict = {
                    'M1': mt5.TIMEFRAME_M1,
                    'M5': mt5.TIMEFRAME_M5,
                    'M15': mt5.TIMEFRAME_M15,
                    'H1': mt5.TIMEFRAME_H1,
                    'H4': mt5.TIMEFRAME_H4,
                    'D1': mt5.TIMEFRAME_D1
                }

                timeframe_mt5 = tf_dict.get(timeframe, mt5.TIMEFRAME_M1)

                # Obter dados usando MT5 diretamente
                rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, count)

                if rates is None or len(rates) == 0:
                    return jsonify({
                        'error': f'Não foi possível obter dados para {symbol}',
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'count': 0,
                        'data': [],
                        'timestamp': datetime.now().isoformat()
                    }), 404

                # Converter para DataFrame e depois para dict
                import pandas as pd
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')

                return jsonify({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'count': len(df),
                    'data': df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].to_dict('records'),
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.error(f"Erro ao obter dados de mercado: {str(e)}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500

    def run(self, host: str = '0.0.0.0', port: int = None, debug: bool = False):
        """Executa a API"""
        port = port or self.config.api_port

        self.logger.info(f"Iniciando API do Bot na porta {port}")
        self.app.run(host=host, port=port, debug=debug)

    def start_background(self, host: str = '0.0.0.0', port: int = None):
        """Inicia a API em background"""
        port = port or self.config.api_port

        def run_api():
            self.run(host=host, port=port, debug=False)

        api_thread = threading.Thread(target=run_api)
        api_thread.daemon = True
        api_thread.start()

        self.logger.info(f"API iniciada em background na porta {port}")
        return api_thread


# Função de conveniência para iniciar API
def create_api_app() -> BotAPIController:
    """Cria instância da API"""
    return BotAPIController()


def run_standalone_api(host: str = '0.0.0.0', port: int = None, debug: bool = False):
    """Executa API standalone"""
    api = create_api_app()
    api.run(host=host, port=port, debug=debug)
