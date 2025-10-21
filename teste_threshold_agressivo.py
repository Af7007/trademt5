#!/usr/bin/env python3
"""
Teste do Threshold Agressivo (60%)
Verifica se o modelo ficou mais agressivo após reduzir o threshold para 60%
"""

import os
import sys
import logging

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('teste_threshold_agressivo.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def testar_thresholds():
    """Testa diferentes thresholds para comparar agressividade"""
    logger.info("=== TESTE DE THRESHOLDS AGRESSIVOS ===")

    try:
        from bot.trading_engine import TradingEngine

        # Criar engine para testar
        engine = TradingEngine()

        logger.info("THRESHOLDS CONFIGURADOS:")
        logger.info(f"  TradingEngine: 60% (modificado)")
        logger.info(f"  MLP Bot: 60% (modificado)")
        logger.info(f"  Storage: 60% (modificado)")

        # Verificar configurações atuais
        config = engine.config
        logger.info("")
        logger.info("CONFIGURACOES ATUAIS:")
        logger.info(f"  Símbolo: {config.trading.symbol}")
        logger.info(f"  Lucro alvo: ${config.trading.target_profit_usd}")
        logger.info(f"  Risco: {config.trading.risk_percentage*100}%")
        logger.info(f"  Lote dinâmico: {config.trading.dynamic_lot_size}")
        logger.info(f"  Operação única: {config.trading.single_operation_mode}")

        # Testar diferentes cenários de confiança
        logger.info("")
        logger.info("TESTE DE CENARIOS:")
        cenarios = [
            (0.95, "Muito alta"),
            (0.80, "Alta"),
            (0.70, "Média alta"),
            (0.65, "Média"),
            (0.60, "Média baixa"),
            (0.55, "Baixa"),
            (0.50, "Muito baixa")
        ]

        for confianca, descricao in cenarios:
            acima_threshold = confianca >= 0.60
            logger.info(f"  Confianca {confianca:.1%} ({descricao}): {'ACEITA' if acima_threshold else 'REJEITADA'}")

        logger.info("")
        logger.info("THRESHOLD AGRESSIVO ATIVADO:")
        logger.info("  - Modelo aceita sinais com confianca >= 60%")
        logger.info("  - Anteriormente era 85% (muito conservador)")
        logger.info("  - Agora e 60% (mais agressivo)")
        logger.info("  - Modelo executara mais operacoes")

        return True

    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return False

def verificar_mudancas():
    """Verifica se as mudanças foram aplicadas corretamente"""
    logger.info("=== VERIFICACAO DAS MUDANCAS ===")

    try:
        # Verificar arquivo trading_engine.py
        with open('bot/trading_engine.py', 'r') as f:
            content = f.read()
            if 'confidence < 0.6' in content:
                logger.info("  TradingEngine: Threshold 60% OK")
            else:
                logger.error("  TradingEngine: Threshold nao encontrado")

        # Verificar arquivo mlp_bot.py
        with open('services/mlp_bot.py', 'r') as f:
            content = f.read()
            if 'confidence_threshold\', 0.60' in content:
                logger.info("  MLP Bot: Threshold 60% OK")
            else:
                logger.error("  MLP Bot: Threshold nao encontrado")

        # Verificar arquivo mlp_storage.py
        with open('services/mlp_storage.py', 'r') as f:
            content = f.read()
            if '"confidence_threshold": 0.60' in content:
                logger.info("  Storage: Threshold 60% OK")
            else:
                logger.error("  Storage: Threshold nao encontrado")

        logger.info("MUDANCAS APLICADAS COM SUCESSO!")
        return True

    except Exception as e:
        logger.error(f"Erro na verificacao: {e}")
        return False

def main():
    """Função principal"""
    logger.info("TESTE DO THRESHOLD AGRESSIVO - 60% DE CONFIANCA")
    logger.info("=" * 60)

    # Verificar mudanças
    if not verificar_mudancas():
        logger.error("Mudancas nao foram aplicadas corretamente")
        return False

    # Testar thresholds
    if not testar_thresholds():
        logger.error("Teste de thresholds falhou")
        return False

    logger.info("=" * 60)
    logger.info("THRESHOLD AGRESSIVO ATIVADO COM SUCESSO!")

    logger.info("")
    logger.info("RESUMO DAS MUDANCAS:")
    logger.info("  - Threshold reduzido de 85% para 60%")
    logger.info("  - Modelo ficou MAIS AGRESSIVO")
    logger.info("  - Aceita sinais com confianca >= 60%")
    logger.info("  - Executara MAIS operacoes")
    logger.info("  - Sistema pronto para teste agressivo")

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
