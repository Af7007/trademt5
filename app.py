import logging
import os
import threading
import time
from flask import Flask
from dotenv import load_dotenv
import MetaTrader5 as mt5
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix
from swagger import swagger_config

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
from scalping_bot import ScalpingBot

load_dotenv()
logger = logging.getLogger(__name__)

# Instância global do bot de scalping
scalping_bot_instance = None

app = Flask(__name__)
app.config['PREFERRED_URL_SCHEME'] = 'https'

swagger = Swagger(app, config=swagger_config)

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
