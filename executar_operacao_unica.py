#!/usr/bin/env python3
"""
Execução da Operação Única do Bot MLP
Executa uma operação única e aguarda o fechamento para atingir $0.50 de lucro
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('operacao_unica.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OperacaoUnicaExecutor:
    """Executor da operação única com monitoramento"""

    def __init__(self):
        self.engine = None
        self.start_time = None
        self.trade_ticket = None
        self.monitoring = False

    def iniciar_bot(self):
        """Inicia o bot de trading"""
        logger.info("=== INICIANDO BOT PARA OPERACAO UNICA ===")

        try:
            from bot.trading_engine import TradingEngine

            self.engine = TradingEngine()

            # Verificar configurações
            config = self.engine.config
            logger.info("Configuracoes atuais:")
            logger.info(f"  Simbolo: {config.trading.symbol}")
            logger.info(f"  Lucro alvo: ${config.trading.target_profit_usd}")
            logger.info(f"  Risco: {config.trading.risk_percentage*100}%")
            logger.info(f"  Lote dinamico: {config.trading.dynamic_lot_size}")
            logger.info(f"  Operacao unica: {config.trading.single_operation_mode}")
            logger.info(f"  Aguardar fechamento: {config.trading.wait_for_position_close}")

            # Iniciar o bot
            if not self.engine.start():
                logger.error("Falha ao iniciar o bot")
                return False

            self.start_time = datetime.now()
            logger.info("Bot iniciado com sucesso!")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}")
            return False

    def monitorar_operacao(self, timeout_minutes=30):
        """Monitora a operação até conclusão"""
        logger.info(f"=== MONITORANDO OPERACAO (timeout: {timeout_minutes}min) ===")

        timeout_seconds = timeout_minutes * 60
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                if not self.engine or not self.engine.is_running:
                    logger.info("Bot nao esta mais rodando")
                    break

                # Obter status atual
                status = self.engine.get_status()
                positions = status.get('positions', [])

                # Verificar se há posições abertas
                if positions:
                    position = positions[0]
                    logger.info(f"Posicao aberta: Ticket {position['ticket']} - {position['type']} {position['symbol']}")
                    logger.info(f"  Volume: {position['volume']}")
                    logger.info(f"  Lucro atual: ${position['profit']:.2f}")

                    # Verificar se atingiu o objetivo de $0.50
                    if position['profit'] >= 0.50:
                        logger.info("OBJETIVO ATINGIDO! Lucro de $0.50 alcancado.")
                        self.trade_ticket = position['ticket']
                        return True

                # Verificar se operação foi executada mas posição já fechou
                if self.engine.trade_executed and not positions:
                    logger.info("Operacao executada e posicao fechada")
                    break

                # Aguardar próximo ciclo
                time.sleep(10)

            except Exception as e:
                logger.error(f"Erro no monitoramento: {e}")
                time.sleep(5)

        logger.info("Timeout atingido ou operacao concluida")
        return False

    def parar_bot(self):
        """Para o bot de trading"""
        if self.engine:
            logger.info("Parando o bot...")
            self.engine.stop()
            logger.info("Bot parado")

    def mostrar_logs_banco(self):
        """Mostra logs detalhados do banco de dados"""
        logger.info("=== LOGS DO BANCO DE DADOS ===")

        try:
            from services.mlp_storage import mlp_storage

            # Obter análises recentes
            logger.info("Analises recentes:")
            analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=10)

            if analyses:
                for analysis in analyses:
                    logger.info(f"  Analise {analysis['id']}: {analysis['signal']} (confianca: {analysis['confidence']:.2f}) - {analysis['timestamp']}")
            else:
                logger.info("  Nenhuma analise encontrada")

            # Obter trades recentes
            logger.info("Trades recentes:")
            trades = mlp_storage.get_trades(symbol='XAUUSDc', days=1)

            if trades:
                for trade in trades:
                    logger.info(f"  Trade {trade['ticket']}: {trade['type']} - Entrada: ${trade['entry_price']:.2f}")
                    logger.info(f"    SL: ${trade['sl_price']:.2f}, TP: ${trade['tp_price']:.2f}")
                    logger.info(f"    Volume: {trade['volume']}, Lucro: ${trade['profit']:.2f}")
                    logger.info(f"    Status: {'Aberto' if not trade['exit_time'] else 'Fechado'}")
            else:
                logger.info("  Nenhum trade encontrado")

            # Obter eventos do bot
            logger.info("Eventos do bot:")
            # Como não temos método direto para eventos, vamos verificar análises com sinais de trade
            if analyses:
                trade_analyses = [a for a in analyses if a['signal'] in ['BUY', 'SELL']]
                for analysis in trade_analyses[:5]:
                    logger.info(f"  Sinal de {analysis['signal']} detectado em {analysis['timestamp']}")

        except Exception as e:
            logger.error(f"Erro ao acessar banco: {e}")

    def gerar_relatorio_final(self):
        """Gera relatório final da operação"""
        logger.info("=== RELATORIO FINAL DA OPERACAO ===")

        try:
            uptime = datetime.now() - self.start_time if self.start_time else "N/A"

            logger.info(f"Tempo de execucao: {uptime}")
            logger.info(f"Ticket da operacao: {self.trade_ticket or 'N/A'}")

            # Mostrar logs do banco
            self.mostrar_logs_banco()

            # Verificar resultado final
            if self.trade_ticket:
                logger.info("OPERACAO UNICA EXECUTADA COM SUCESSO!")
                logger.info(f"Objetivo: $0.50 de lucro")
                logger.info(f"Status: Posicao aberta e sendo monitorada")
            else:
                logger.info("Operacao ainda nao foi executada ou ja foi fechada")

        except Exception as e:
            logger.error(f"Erro ao gerar relatorio: {e}")

def main():
    """Função principal"""
    logger.info("EXECUCAO DA OPERACAO UNICA - OBJETIVO: $0.50 DE LUCRO")
    logger.info("=" * 70)

    executor = OperacaoUnicaExecutor()

    try:
        # Iniciar bot
        if not executor.iniciar_bot():
            logger.error("Falha ao iniciar bot")
            return False

        # Monitorar operação
        objetivo_atingido = executor.monitorar_operacao(timeout_minutes=30)

        # Parar bot
        executor.parar_bot()

        # Gerar relatório
        executor.gerar_relatorio_final()

        logger.info("=" * 70)
        if objetivo_atingido:
            logger.info("SUCESSO! Objetivo de $0.50 alcancado!")
        else:
            logger.info("Operacao concluida (timeout ou fechamento)")

        return objetivo_atingido

    except KeyboardInterrupt:
        logger.info("Execucao interrompida pelo usuario")
        executor.parar_bot()
        return False
    except Exception as e:
        logger.error(f"Erro fatal na execucao: {e}")
        executor.parar_bot()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Erro na execucao principal: {e}")
        sys.exit(1)
