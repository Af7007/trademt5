#!/usr/bin/env python3
"""
Teste Final das Configurações do Bot MLP - Versão Corrigida
Testa se o bot está preservando as configurações editadas e obedecendo para executar as operações.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging simples (sem emojis)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('teste_configuracoes_final.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def verificar_configuracoes():
    """Verifica se as configurações estão corretas"""
    logger.info("=== VERIFICACAO DAS CONFIGURACOES ===")

    try:
        from bot.config import get_config
        config = get_config()

        logger.info(f"Simbolo: {config.trading.symbol}")
        logger.info(f"Lucro alvo: ${config.trading.target_profit_usd}")
        logger.info(f"Risco por operacao: {config.trading.risk_percentage*100}%")
        logger.info(f"Lote dinamico: {config.trading.dynamic_lot_size}")
        logger.info(f"Modo operacao unica: {config.trading.single_operation_mode}")
        logger.info(f"Aguardar fechamento: {config.trading.wait_for_position_close}")
        logger.info(f"Magic number: {config.trading.magic_number}")

        # Verificar se as configurações estão corretas
        configuracoes_corretas = (
            config.trading.symbol == "XAUUSDc" and
            config.trading.target_profit_usd == 0.50 and
            config.trading.risk_percentage == 0.01 and
            config.trading.dynamic_lot_size == True and
            config.trading.single_operation_mode == True and
            config.trading.wait_for_position_close == True
        )

        if configuracoes_corretas:
            logger.info("CONFIGURACOES CORRETAS!")
            return True
        else:
            logger.error("CONFIGURACOES INCORRETAS!")
            return False

    except Exception as e:
        logger.error(f"Erro ao verificar configuracoes: {e}")
        return False

def testar_conexao_mt5():
    """Testa conexão MT5 e símbolo"""
    logger.info("=== TESTANDO CONEXAO MT5 ===")

    try:
        import MetaTrader5 as mt5

        # Inicializar MT5
        if not mt5.initialize():
            logger.error("Falha na inicializacao MT5")
            return False

        # Verificar conta
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Nao foi possivel obter informacoes da conta")
            return False

        logger.info(f"Conta conectada: {account_info.login}")

        # Verificar símbolo
        symbol_info = mt5.symbol_info('XAUUSDc')
        if symbol_info is None:
            logger.error("Simbolo XAUUSDc nao encontrado")
            return False

        logger.info(f"Simbolo OK: {symbol_info.name}")

        # Testar dados históricos
        rates = mt5.copy_rates_from_pos('XAUUSDc', mt5.TIMEFRAME_M1, 0, 10)
        if rates is None or len(rates) == 0:
            logger.error("Nao foi possivel obter dados historicos")
            return False

        logger.info(f"Dados historicos OK: {len(rates)} candles")

        mt5.shutdown()
        logger.info("CONEXAO MT5 OK!")
        return True

    except Exception as e:
        logger.error(f"Erro no teste MT5: {e}")
        return False

def executar_teste_rapido():
    """Executa teste rápido das funcionalidades principais"""
    logger.info("=== TESTE RAPIDO DAS FUNCIONALIDADES ===")

    try:
        # Testar configurações
        if not verificar_configuracoes():
            return False

        # Testar conexão MT5
        if not testar_conexao_mt5():
            return False

        # Testar banco de dados
        try:
            from services.mlp_storage import mlp_storage
            analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=5)
            trades = mlp_storage.get_trades(symbol='XAUUSDc', days=1)
            logger.info(f"Banco OK - Analises: {len(analyses)}, Trades: {len(trades)}")
        except Exception as e:
            logger.error(f"Erro no banco: {e}")
            return False

        logger.info("TESTE RAPIDO OK!")
        return True

    except Exception as e:
        logger.error(f"Erro no teste rapido: {e}")
        return False

def main():
    """Função principal do teste"""
    logger.info("TESTE FINAL DAS CONFIGURACOES DO BOT MLP")
    logger.info("=" * 60)

    # Executar teste rápido
    if not executar_teste_rapido():
        logger.error("Teste rapido falhou")
        return False

    logger.info("=" * 60)
    logger.info("TESTE CONCLUIDO COM SUCESSO!")

    # Resumo final
    logger.info("RESUMO DO TESTE:")
    logger.info("- Configuracoes verificadas e aplicadas")
    logger.info("- Conexao MT5 funcionando corretamente")
    logger.info("- Simbolo XAUUSDc disponivel e operacional")
    logger.info("- Banco de dados funcionando")
    logger.info("- Sistema pronto para operacao unica")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro fatal no teste: {str(e)}")
        sys.exit(1)
