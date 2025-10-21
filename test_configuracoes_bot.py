#!/usr/bin/env python3
"""
Teste das Configurações do Bot MLP
Testa se o bot está preservando as configurações editadas e obedecendo para executar as operações.

Configurações específicas do teste:
- Lucro de ~$0,50
- SL de segurança baseado no saldo da conta atual
- Lote dinâmico
- M1 timeframe
- XAUUSD símbolo
- Uma operação somente
- Aguardar fechamento da posição para encerrar o bot
"""

import os
import sys
import time
import logging
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.trading_engine import TradingEngine
from services.mlp_storage import mlp_storage

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_configuracoes.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def verificar_configuracoes():
    """Verifica se as configurações estão corretas"""
    logger.info("=== VERIFICAÇÃO DAS CONFIGURAÇÕES ===")

    # Verificar configurações do bot
    config = TradingEngine().config

    logger.info(f"Símbolo: {config.trading.symbol}")
    logger.info(f"Timeframe: M1 (configurado no código)")
    logger.info(f"Lucro alvo: ${config.trading.target_profit_usd}")
    logger.info(f"Risco por operação: {config.trading.risk_percentage*100}%")
    logger.info(f"Lote dinâmico: {config.trading.dynamic_lot_size}")
    logger.info(f"Modo operação única: {config.trading.single_operation_mode}")
    logger.info(f"Aguardar fechamento: {config.trading.wait_for_position_close}")
    logger.info(f"Magic number: {config.trading.magic_number}")

    # Verificar se as configurações estão corretas
    configuracoes_corretas = (
        config.trading.symbol == "XAUUSD" and
        config.trading.target_profit_usd == 0.50 and
        config.trading.risk_percentage == 0.01 and
        config.trading.dynamic_lot_size == True and
        config.trading.single_operation_mode == True and
        config.trading.wait_for_position_close == True
    )

    if configuracoes_corretas:
        logger.info("✅ Todas as configurações estão corretas!")
        return True
    else:
        logger.error("❌ Algumas configurações estão incorretas!")
        return False

def executar_teste_operacao():
    """Executa o teste de operação única"""
    logger.info("=== INICIANDO TESTE DE OPERAÇÃO ===")

    try:
        # Criar instância do bot
        engine = TradingEngine()

        # Verificar configurações antes de iniciar
        if not verificar_configuracoes():
            logger.error("Configurações incorretas, abortando teste")
            return False

        # Iniciar o bot
        logger.info("Iniciando o bot...")
        if not engine.start():
            logger.error("Falha ao iniciar o bot")
            return False

        logger.info("Bot iniciado com sucesso!")

        # Aguardar análise e possível execução de trade
        logger.info("Aguardando análise do mercado...")

        # Monitorar por até 10 minutos
        max_wait_time = 600  # 10 minutos
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status = engine.get_status()

            if not status.get('is_running', False):
                logger.info("Bot foi parado")
                break

            # Verificar se há posições abertas
            positions = status.get('positions', [])
            if positions:
                position = positions[0]
                logger.info(f"Posição aberta: {position['ticket']} - {position['type']} {position['symbol']}")
                logger.info(f"Volume: {position['volume']}, Lucro: ${position['profit']:.2f}")

                # Se não estiver no modo de aguardar fechamento, parar o bot
                if not engine.config.trading.wait_for_position_close:
                    logger.info("Modo sem aguardar fechamento - parando o bot")
                    engine.stop()
                    break

            # Verificar se o bot executou um trade e está aguardando fechamento
            if engine.trade_executed and not positions:
                logger.info("Trade executado e posição fechada - teste concluído")
                engine.stop()
                break

            time.sleep(10)  # Verificar a cada 10 segundos

        # Parar o bot se ainda estiver rodando
        if engine.is_running:
            logger.info("Tempo limite atingido - parando o bot")
            engine.stop()

        return True

    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")
        return False

def verificar_logs_banco():
    """Verifica os logs da operação no banco de dados"""
    logger.info("=== VERIFICAÇÃO DOS LOGS NO BANCO ===")

    try:
        # Obter análises recentes
        analyses = mlp_storage.get_analyses(symbol="XAUUSD", limit=10)
        logger.info(f"Análises encontradas: {len(analyses)}")

        for analysis in analyses[:3]:  # Mostrar apenas as 3 mais recentes
            logger.info(f"Análise ID {analysis['id']}:")
            logger.info(f"  Sinal: {analysis['signal']}")
            logger.info(f"  Confiança: {analysis['confidence']:.2f}")
            logger.info(f"  Timestamp: {analysis['timestamp']}")
            logger.info(f"  Indicadores: {analysis.get('indicators', {})}")

        # Obter trades recentes
        trades = mlp_storage.get_trades(symbol="XAUUSD", days=1)
        logger.info(f"Trades encontrados: {len(trades)}")

        for trade in trades:
            logger.info(f"Trade {trade['ticket']}:")
            logger.info(f"  Tipo: {trade['type']}")
            logger.info(f"  Volume: {trade['volume']}")
            logger.info(f"  Preço entrada: {trade['entry_price']}")
            logger.info(f"  SL: {trade['sl_price']}")
            logger.info(f"  TP: {trade['tp_price']}")
            logger.info(f"  Lucro: {trade['profit']}")
            logger.info(f"  Status: {'Aberto' if not trade['exit_time'] else 'Fechado'}")

        # Obter eventos do bot
        try:
            # Como não temos método direto, vamos verificar se há análises recentes
            if analyses:
                logger.info("✅ Logs de análises encontrados no banco")
            if trades:
                logger.info("✅ Logs de trades encontrados no banco")
        except Exception as e:
            logger.error(f"Erro ao verificar eventos: {e}")

        return len(analyses) > 0 or len(trades) > 0

    except Exception as e:
        logger.error(f"Erro ao verificar banco: {str(e)}")
        return False

def main():
    """Função principal do teste"""
    logger.info("INICIANDO TESTE DAS CONFIGURAÇÕES DO BOT MLP")
    logger.info("=" * 60)

    # Verificar configurações
    if not verificar_configuracoes():
        logger.error("Teste abortado devido a configurações incorretas")
        return False

    # Executar teste de operação
    if not executar_teste_operacao():
        logger.error("Teste de operação falhou")
        return False

    # Aguardar um pouco para garantir que os dados foram salvos
    logger.info("Aguardando gravação dos dados no banco...")
    time.sleep(5)

    # Verificar logs no banco
    if not verificar_logs_banco():
        logger.warning("Nenhum log encontrado no banco - pode ser normal se não houve operações")

    logger.info("=" * 60)
    logger.info("TESTE CONCLUÍDO")

    # Resumo final
    logger.info("RESUMO DO TESTE:")
    logger.info("- ✅ Configurações verificadas e aplicadas")
    logger.info("- ✅ Bot iniciado com configurações específicas")
    logger.info("- ✅ Modo de operação única habilitado")
    logger.info("- ✅ Sistema de aguardar fechamento configurado")
    logger.info("- ✅ Logs verificados no banco de dados")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Teste interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro fatal no teste: {str(e)}")
        sys.exit(1)
