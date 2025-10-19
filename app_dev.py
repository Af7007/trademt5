import logging
import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from flasgger import Swagger
from werkzeug.middleware.proxy_fix import ProxyFix

# Import routes (dev versions without MT5)
from routes.health_dev import health_bp
from routes.error_dev import error_bp

load_dotenv()
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, config=swagger_config)

# Register basic blueprints
app.register_blueprint(health_bp)
app.register_blueprint(error_bp)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route('/')
def index():
    """
    API Root
    ---
    responses:
      200:
        description: API information
    """
    return jsonify({
        "message": "MT5 API - Development Mode",
        "version": "2.0.0",
        "status": "running",
        "note": "MetaTrader5 not connected in dev mode",
        "docs": "/apidocs/"
    })

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Starting MT5 API in DEVELOPMENT mode (no MT5 connection)")
    logger.info("=" * 60)

    port = int(os.environ.get('MT5_API_PORT', 5001))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
