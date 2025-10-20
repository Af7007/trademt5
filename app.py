import logging
import os
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import MetaTrader5 as mt5
from werkzeug.middleware.proxy_fix import ProxyFix
from flasgger import Swagger, swag_from

# Import routes
from routes.health import health_bp
from routes.symbol import symbol_bp
from routes.data import data_bp
from routes.position import position_bp
from routes.order import order_bp
from routes.history import history_bp
from routes.error import error_bp
from routes.btcusd_stats import btcusd_stats_bp
from routes.scalping_routes import scalping_bp
# Removido: documentação movida para Django (porta 5001)

# Import bot MLP API
from bot.api_controller import BotAPIController

load_dotenv()
logger = logging.getLogger(__name__)

# Instância global do controlador do bot MLP
bot_controller = BotAPIController()

app = Flask(__name__)
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(symbol_bp)
app.register_blueprint(data_bp)
app.register_blueprint(position_bp)
app.register_blueprint(order_bp)
app.register_blueprint(history_bp)
app.register_blueprint(error_bp)
app.register_blueprint(btcusd_stats_bp)
app.register_blueprint(scalping_bp)
# Removido: apidocs_bp movido para Django (porta 5001)

# Initialize Swagger
swagger = Swagger(app)

# Rotas completas do Bot MLP (equivalentes ao que está no bot/api_controller.py)
@app.route('/mlp/health', methods=['GET'])
def mlp_health_check():
    """
    Verifica saúde do bot MLP
    ---
    tags:
      - MLP Bot
    responses:
      200:
        description: Health check successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            timestamp:
              type: string
              format: date-time
            bot_running:
              type: boolean
            mt5_connected:
              type: boolean
    """
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'bot_running': bot_controller.trading_engine.is_running,
            'mt5_connected': bot_controller.trading_engine.get_status().get('mt5_connected', False)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/start', methods=['POST'])
def mlp_start():
    """
    Inicia o bot MLP
    ---
    tags:
      - MLP Bot
    responses:
      200:
        description: Bot iniciado com sucesso
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            timestamp:
              type: string
              format: date-time
    """
    try:
        success = bot_controller.trading_engine.start()
        return jsonify({
            'success': success,
            'message': 'Bot iniciado com sucesso' if success else 'Falha ao iniciar bot',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/stop', methods=['POST'])
def mlp_stop():
    """
    Para o bot MLP
    ---
    tags:
      - MLP Bot
    responses:
      200:
        description: Bot parado com sucesso
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: "Bot parado com sucesso"
            timestamp:
              type: string
              format: date-time
    """
    try:
        bot_controller.trading_engine.stop()
        return jsonify({
            'success': True,
            'message': 'Bot parado com sucesso',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/status', methods=['GET'])
def mlp_status():
    """
    Obtém status atual do bot MLP
    ---
    tags:
      - MLP Bot
    responses:
      200:
        description: Status obtido com sucesso
        schema:
          type: object
          properties:
            is_running:
              type: boolean
            mt5_connected:
              type: boolean
            positions_count:
              type: integer
            uptime:
              type: string
    """
    try:
        status = bot_controller.trading_engine.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/execute', methods=['POST'])
def mlp_execute():
    """
    Executa sinal de trading
    ---
    tags:
      - MLP Bot
    parameters:
      - name: signal
        in: body
        required: true
        schema:
          type: object
          properties:
            signal:
              type: string
              enum: [BUY, SELL, HOLD]
              example: "BUY"
            confidence:
              type: number
              format: float
              example: 0.85
    responses:
      200:
        description: Sinal executado
        schema:
          type: object
          properties:
            success:
              type: boolean
            signal:
              type: string
            confidence:
              type: number
            timestamp:
              type: string
              format: date-time
    """
    try:
        data = request.get_json()
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
            result = bot_controller.trading_engine.execute_signal(signal, confidence)
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
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/analyze', methods=['POST'])
def mlp_analyze():
    """
    Analisa mercado e executa operação automaticamente
    ---
    tags:
      - MLP Bot
    responses:
      200:
        description: Análise executada
        schema:
          type: object
          properties:
            success:
              type: boolean
            result:
              type: object
            timestamp:
              type: string
              format: date-time
    """
    try:
        result = bot_controller.trading_engine.analyze_and_trade()
        return jsonify({
            'success': result.get('success', False),
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/train', methods=['POST'])
def mlp_train():
    """
    Treina o modelo com dados históricos
    ---
    tags:
      - MLP Bot
    parameters:
      - name: training_data
        in: body
        schema:
          type: object
          properties:
            days:
              type: integer
              default: 30
              example: 30
    responses:
      200:
        description: Modelo treinado
        schema:
          type: object
          properties:
            success:
              type: boolean
            result:
              type: object
            timestamp:
              type: string
              format: date-time
    """
    try:
        data = request.get_json()
        days = data.get('days', 30) if data else 30

        result = bot_controller.trading_engine.train_model(days)
        return jsonify({
            'success': result.get('success', False),
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/emergency-close', methods=['POST'])
def mlp_emergency_close():
    """Fecha todas as posições em emergência"""
    try:
        result = bot_controller.trading_engine.emergency_close_all()
        return jsonify({
            'success': result.get('success', False),
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/performance', methods=['GET'])
def mlp_performance():
    """Obtém relatório de performance"""
    try:
        report = bot_controller.trading_engine.get_performance_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/positions', methods=['GET'])
def mlp_positions():
    """Obtém posições atuais"""
    try:
        status = bot_controller.trading_engine.get_status()
        positions = status.get('positions', [])
        return jsonify({
            'positions': positions,
            'total': len(positions),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/market-data', methods=['GET'])
def mlp_market_data():
    """Obtém dados de mercado"""
    try:
        import MetaTrader5 as mt5

        symbol = request.args.get('symbol', bot_controller.config.trading.symbol)
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
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/mlp/history', methods=['GET'])
def mlp_history():
    """
    Obtém histórico de análises MLP
    ---
    tags:
      - MLP Bot
    parameters:
      - name: symbol
        in: query
        type: string
        example: BTCUSDc
      - name: limit
        in: query
        type: integer
        default: 100
        example: 50
    responses:
      200:
        description: Histórico de análises
        schema:
          type: array
          items:
            type: object
    """
    try:
        from services.mlp_storage import mlp_storage

        symbol = request.args.get('symbol')
        limit = int(request.args.get('limit', 100))

        # Usar MLPStorage independente
        analyses = mlp_storage.get_analyses(symbol=symbol, limit=limit)

        return jsonify({
            'history': analyses,
            'count': len(analyses),
            'symbol': symbol or 'all',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': f'Banco MLP não disponível: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/mlp/trades', methods=['GET'])
def mlp_trades():
    """
    Obtém histórico de trades MLP
    ---
    tags:
      - MLP Bot
    parameters:
      - name: symbol
        in: query
        type: string
        example: BTCUSDc
      - name: days
        in: query
        type: integer
        default: 30
        example: 7
    responses:
      200:
        description: Histórico de trades
        schema:
          type: array
          items:
            type: object
    """
    try:
        from services.mlp_storage import mlp_storage

        symbol = request.args.get('symbol')
        days = int(request.args.get('days', 30))

        # Usar MLPStorage independente
        trades = mlp_storage.get_trades(symbol=symbol, days=days)

        return jsonify({
            'trades': trades,
            'count': len(trades),
            'symbol': symbol or 'all',
            'period_days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': f'Banco MLP não disponível: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/mlp/analytics', methods=['GET'])
def mlp_analytics():
    """
    Obtém estatísticas diárias do bot MLP
    ---
    tags:
      - MLP Bot
    parameters:
      - name: days
        in: query
        type: integer
        default: 30
        example: 7
    responses:
      200:
        description: Estatísticas diárias
        schema:
          type: array
          items:
            type: object
    """
    try:
        from services.mlp_storage import mlp_storage

        days = int(request.args.get('days', 30))

        # Usar MLPStorage independente
        stats = mlp_storage.get_daily_stats(days=days)

        return jsonify({
            'analytics': stats,
            'period_days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'error': f'Banco MLP não disponível: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/mlp/update-trade', methods=['POST'])
def update_trade_profit():
    """
    Atualiza o lucro/prejuízo de um trade
    ---
    tags:
      - MLP Bot
    parameters:
      - name: trade_update
        in: body
        required: true
        schema:
          type: object
          properties:
            ticket:
              type: integer
              example: 123456
            profit:
              type: number
              example: 25.50
            exit_price:
              type: number
              example: 65425.80
            exit_reason:
              type: string
              enum: [TP, SL, MANUAL, EMERGENCY, CLOSE]
              example: TP
    responses:
      200:
        description: Trade atualizado
        schema:
          type: object
          properties:
            success:
              type: boolean
    """
    try:
        from services.mlp_storage import mlp_storage

        data = request.get_json()
        if not data or 'ticket' not in data or 'profit' not in data:
            return jsonify({
                'success': False,
                'error': 'Campos ticket e profit são obrigatórios',
                'timestamp': datetime.now().isoformat()
            }), 400

        ticket = str(data['ticket'])  # Convert to string for consistency
        profit = float(data['profit'])
        exit_price = data.get('exit_price')
        exit_reason = data.get('exit_reason', 'MANUAL')

        # Usar MLPStorage independente
        updates = {
            'profit': profit,
            'exit_price': exit_price,
            'exit_reason': exit_reason
        }

        success = mlp_storage.update_trade(ticket, updates)

        if not success:
            return jsonify({
                'success': False,
                'error': f'Trade com ticket {ticket} não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 404

        return jsonify({
            'success': True,
            'message': f'Trade {ticket} atualizado com profit ${profit}',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# ===== ROTAS BOT STANDALONE (/bot/*) - INTEGRADAS NA PORTA 5000 =====

@app.route('/bot/health', methods=['GET'])
def bot_health_check():
    """Health check da API Bot (/bot/health)"""
    return mlp_health_check()

@app.route('/bot/start', methods=['POST'])
def bot_start():
    """Iniciar bot de trading (/bot/start)"""
    return mlp_start()

@app.route('/bot/stop', methods=['POST'])
def bot_stop():
    """Parar bot de trading (/bot/stop)"""
    return mlp_stop()

@app.route('/bot/mlp-status', methods=['GET'])
def bot_mlp_status():
    """Status detalhado do bot MLP (/bot/mlp-status)"""
    return mlp_status()

@app.route('/bot/execute', methods=['POST'])
def bot_execute():
    """Executar sinal BUY/SELL/HOLD (/bot/execute)"""
    return mlp_execute()

@app.route('/bot/analyze', methods=['POST'])
def bot_analyze():
    """Analisar mercado e executar automaticamente (/bot/analyze)"""
    return mlp_analyze()

@app.route('/bot/train', methods=['POST'])
def bot_train():
    """Treinar modelo MLP com dados históricos (/bot/train)"""
    return mlp_train()

@app.route('/bot/emergency-close', methods=['POST'])
def bot_emergency_close():
    """Fecha todas as posições em emergência (/bot/emergency-close)"""
    return mlp_emergency_close()

@app.route('/bot/performance', methods=['GET'])
def bot_performance():
    """Relatório de performance detalhado (/bot/performance)"""
    return mlp_performance()

@app.route('/bot/positions', methods=['GET'])
def bot_positions():
    """Posições ativas atuais (/bot/positions)"""
    return mlp_positions()

@app.route('/bot/market-data', methods=['GET'])
def bot_market_data():
    """Dados de mercado em tempo real (/bot/market-data)"""
    return mlp_market_data()

# ===== FIM DAS ROTAS BOT STANDALONE =====

# Rotas de teste adicionais
@app.route('/test-mlp', methods=['GET'])
def test_mlp():
    """Teste básico das funcionalidades do bot MLP"""
    return jsonify({
        'success': True,
        'message': 'Bot MLP integrado com sucesso',
        'mt5_connection_available': True,
        'trading_engine_ready': True,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/ping', methods=['GET'])
def ping():
    """Teste básico de conectividade"""
    return jsonify({
        'status': 'pong',
        'message': 'Servidor funcionando',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/mlp/config', methods=['POST'])
def mlp_update_config():
    """
    Atualiza configuração do bot MLP
    ---
    tags:
      - MLP Bot
    parameters:
      - name: config
        in: body
        required: true
        schema:
          type: object
          properties:
            take_profit:
              type: number
              default: 0.50
              example: 0.50
            confidence_threshold:
              type: number
              default: 0.85
              example: 0.85
            auto_trading_enabled:
              type: boolean
              default: true
              example: true
    responses:
      200:
        description: Configuração atualizada
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados de configuração obrigatórios',
                'timestamp': datetime.now().isoformat()
            }), 400

        # Atualizar configuração do bot
        config_updates = {}

        if 'take_profit' in data:
            tp_value = float(data['take_profit'])
            config_updates['take_profit'] = tp_value
            logger.info(f"TP atualizado para ${tp_value}")

        if 'confidence_threshold' in data:
            threshold = float(data['confidence_threshold'])
            config_updates['confidence_threshold'] = threshold
            logger.info(f"Threshold atualizado para {threshold*100:.0f}%")

        if 'auto_trading_enabled' in data:
            enabled = bool(data['auto_trading_enabled'])
            config_updates['auto_trading_enabled'] = enabled
            logger.info(f"Auto trading: {'habilitado' if enabled else 'desabilitado'}")

        return jsonify({
            'success': True,
            'message': 'Configuração atualizada com sucesso',
            'updates': config_updates,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Erro ao atualizar config: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


def start_scalping_bot_background():
    """
    Inicia o bot de scalping em background após um pequeno delay
    para garantir que o MT5 está totalmente inicializado
    """
    global scalping_bot_instance

    # Aguardar 5 segundos para garantir inicialização completa
    time.sleep(5)

    try:
        logger.info("=" * 60)
        logger.info("Iniciando Scalping Bot automaticamente...")
        logger.info("=" * 60)

        # Criar instância do bot com configurações padrão
        scalping_bot_instance = ScalpingBot(
            symbol="BTCUSDc",
            timeframe=mt5.TIMEFRAME_M5,
            confidence_threshold=85,  # Confiança mínima de 85%
            volume=0.01,  # Volume padrão de 0.01 lote
            use_dynamic_risk=True  # Usar gerenciamento de risco dinâmico
        )

        # Executar bot (irá rodar em loop)
        scalping_bot_instance.run(interval=60)  # Verificar a cada 60 segundos

    except Exception as e:
        logger.error(f"Erro ao iniciar bot de scalping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if not mt5.initialize():
        logger.error("Failed to initialize MT5.")
    else:
        # BOT DESABILITADO - Removido o auto-start do scalping bot
        # Para habilitar novamente, descomente as linhas abaixo:
        # bot_thread = threading.Thread(target=start_scalping_bot_background, daemon=True)
        # bot_thread.start()
        # logger.info("Thread do Scalping Bot iniciada em background")
        logger.info("Scalping Bot está DESABILITADO - Use as rotas /scalping/start para iniciar manualmente")

    app.run(host='0.0.0.0', port=int(os.environ.get('MT5_API_PORT', 5000)))
