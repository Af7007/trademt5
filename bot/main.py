#!/usr/bin/env python3
"""
Bot de Trading MT5 com MLP Neural Network - Arquivo Principal
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Adicionar diretório pai ao path para importar módulos
sys.path.append(str(Path(__file__).parent.parent))

from .config import get_config, DEFAULT_CONFIG
from .trading_engine import TradingEngine
from .api_controller import BotAPIController, run_standalone_api


def setup_logging(config) -> None:
    """Configura sistema de logging"""
    # Criar diretório de logs
    log_dir = Path("bot/logs")
    log_dir.mkdir(exist_ok=True)

    # Configurar formato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configurar logging para arquivo
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Configurar logging para bibliotecas externas
    logging.getLogger('tensorflow').setLevel(logging.WARNING)
    logging.getLogger('MetaTrader5').setLevel(logging.INFO)


def create_directories() -> None:
    """Cria diretórios necessários"""
    directories = [
        "bot/logs",
        "bot/models",
        "bot/data",
        "bot/reports"
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def train_model_only(args) -> None:
    """Modo apenas treinamento"""
    logger = logging.getLogger(__name__)
    logger.info("Iniciando modo de treinamento...")

    config = get_config()
    setup_logging(config)

    engine = TradingEngine()

    # Conectar ao MT5 para obter dados
    if not engine.mt5_connector.connect():
        logger.error("Falha na conexão com MT5")
        sys.exit(1)

    # Treinar modelo
    days = args.days if hasattr(args, 'days') else 30
    result = engine.train_model(days)

    if result.get('success'):
        logger.info("Treinamento concluído com sucesso!")
        logger.info(f"Dados processados: {result.get('data_points', 0)}")
        logger.info(f"Épocas treinadas: {result.get('training_time', 0)}")
    else:
        logger.error(f"Falha no treinamento: {result.get('error')}")
        sys.exit(1)


def run_api_only(args) -> None:
    """Modo apenas API"""
    logger = logging.getLogger(__name__)
    logger.info("Iniciando modo API...")

    config = get_config()
    setup_logging(config)

    # Criar e executar API
    api = BotAPIController()

    host = args.host if hasattr(args, 'host') else '0.0.0.0'
    port = args.port if hasattr(args, 'port') else config.api_port
    debug = args.debug if hasattr(args, 'debug') else False

    logger.info(f"API iniciando em {host}:{port}")
    api.run(host=host, port=port, debug=debug)


def run_full_bot(args) -> None:
    """Modo bot completo (API + Trading Engine)"""
    logger = logging.getLogger(__name__)
    logger.info("Iniciando bot completo...")

    config = get_config()
    setup_logging(config)

    # Criar diretórios
    create_directories()

    # Inicializar componentes
    trading_engine = TradingEngine()
    api_controller = BotAPIController()

    # Substituir engine da API pelo nosso
    api_controller.trading_engine = trading_engine

    # Iniciar bot se solicitado
    if args.start_bot:
        logger.info("Iniciando bot de trading...")
        if not trading_engine.start():
            logger.error("Falha ao iniciar bot de trading")
            sys.exit(1)
        logger.info("Bot de trading iniciado")

    # Iniciar API
    host = args.host if hasattr(args, 'host') else '0.0.0.0'
    port = args.port if hasattr(args, 'port') else config.api_port
    debug = args.debug if hasattr(args, 'debug') else False

    logger.info(f"API iniciando em {host}:{port}")
    api_controller.run(host=host, port=port, debug=debug)


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Bot de Trading MT5 com MLP')

    # Subcomandos
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando de treinamento
    train_parser = subparsers.add_parser('train', help='Treinar modelo MLP')
    train_parser.add_argument('--days', type=int, default=30, help='Dias de dados históricos (padrão: 30)')
    train_parser.add_argument('--config', help='Arquivo de configuração')

    # Comando API apenas
    api_parser = subparsers.add_parser('api', help='Executar apenas API')
    api_parser.add_argument('--host', default='0.0.0.0', help='Host para API (padrão: 0.0.0.0)')
    api_parser.add_argument('--port', type=int, help='Porta para API')
    api_parser.add_argument('--debug', action='store_true', help='Debug mode')

    # Comando bot completo
    bot_parser = subparsers.add_parser('bot', help='Executar bot completo')
    bot_parser.add_argument('--host', default='0.0.0.0', help='Host para API (padrão: 0.0.0.0)')
    bot_parser.add_argument('--port', type=int, help='Porta para API')
    bot_parser.add_argument('--start-bot', action='store_true', help='Iniciar bot automaticamente')
    bot_parser.add_argument('--debug', action='store_true', help='Debug mode')

    # Parse argumentos
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Carregar configuração se especificada
    if hasattr(args, 'config') and args.config:
        os.environ['USE_ENV_CONFIG'] = 'true'

    # Executar comando
    try:
        if args.command == 'train':
            train_model_only(args)
        elif args.command == 'api':
            run_api_only(args)
        elif args.command == 'bot':
            run_full_bot(args)
    except KeyboardInterrupt:
        print("\nInterrupção pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
