#!/usr/bin/env python3
"""
Diagnóstico detalhado do problema no TradingEngine
"""

import sys
import os
import logging
import traceback

# Adicionar diretórios ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_trading_engine.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def diagnosticar_problema():
    """Diagnosticar o problema específico no trading_engine"""
    logger.info("=== INICIANDO DIAGNÓSTICO DETALHADO ===")

    try:
        # 1. Testar importações básicas
        logger.info("1. Testando importações básicas...")
        import MetaTrader5 as mt5
        import pandas as pd
        import numpy as np
        logger.info("✅ Importações básicas OK")

        # 2. Testar inicialização MT5
        logger.info("2. Testando inicialização MT5...")
        if not mt5.initialize():
            logger.error("❌ Falha na inicialização MT5")
            return False

        logger.info("✅ MT5 inicializado com sucesso")

        # 3. Verificar conexão e conta
        logger.info("3. Verificando conexão e conta...")
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("❌ Não foi possível obter informações da conta")
            return False

        logger.info(f"✅ Conta conectada: {account_info.login}")

        # 4. Verificar símbolo específico
        logger.info("4. Verificando símbolo XAUUSDc...")
        symbol_info = mt5.symbol_info('XAUUSDc')
        if symbol_info is None:
            logger.error("❌ Símbolo XAUUSDc não encontrado")
            return False

        logger.info(f"✅ Símbolo encontrado: {symbol_info.name}")
        logger.info(f"   Visível: {symbol_info.visible}")
        logger.info(f"   Selecionado: {symbol_info.select}")

        # 5. Testar obtenção de dados históricos
        logger.info("5. Testando obtenção de dados históricos...")
        rates = mt5.copy_rates_from_pos('XAUUSDc', mt5.TIMEFRAME_M1, 0, 60)

        logger.info(f"   Rates raw: {rates}")
        logger.info(f"   Rates type: {type(rates)}")

        if rates is None:
            logger.error("❌ Rates retornou None")
            return False

        if len(rates) == 0:
            logger.error("❌ Rates retornou array vazio")
            return False

        logger.info(f"✅ Dados históricos obtidos: {len(rates)} candles")

        # 6. Testar conversão para DataFrame
        logger.info("6. Testando conversão para DataFrame...")
        try:
            market_data = pd.DataFrame(rates)
            market_data['time'] = pd.to_datetime(market_data['time'], unit='s')
            market_data = market_data[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
            logger.info(f"✅ DataFrame criado: {len(market_data)} linhas")
        except Exception as e:
            logger.error(f"❌ Erro na conversão DataFrame: {e}")
            return False

        # 7. Testar configurações do bot
        logger.info("7. Testando configurações do bot...")
        try:
            from bot.config import get_config
            config = get_config()
            logger.info(f"✅ Configuração carregada: {config.trading.symbol}")
        except Exception as e:
            logger.error(f"❌ Erro no carregamento de configuração: {e}")
            return False

        # 8. Testar contexto completo do trading_engine
        logger.info("8. Testando contexto completo do trading_engine...")
        try:
            from bot.trading_engine import TradingEngine

            # Criar instância sem iniciar
            engine = TradingEngine()
            logger.info("✅ TradingEngine instanciado")

            # Testar configuração
            logger.info(f"   Símbolo configurado: {engine.config.trading.symbol}")
            logger.info(f"   Sequence length: {engine.config.mlp.sequence_length}")

            # Testar obtenção de dados no contexto do engine
            test_rates = mt5.copy_rates_from_pos(
                engine.config.trading.symbol,
                mt5.TIMEFRAME_M1,
                0,
                engine.config.mlp.sequence_length
            )

            if test_rates is None or len(test_rates) == 0:
                logger.error("❌ Problema reproduzido no contexto do engine")
                logger.error(f"   Símbolo: {engine.config.trading.symbol}")
                logger.error(f"   Sequence length: {engine.config.mlp.sequence_length}")
                return False

            logger.info("✅ Dados obtidos no contexto do engine")

        except Exception as e:
            logger.error(f"❌ Erro no contexto do trading_engine: {e}")
            logger.error(traceback.format_exc())
            return False

        # 9. Testar modelo MLP
        logger.info("9. Testando modelo MLP...")
        try:
            from bot.mlp_model import MLPModel
            model = MLPModel()
            model.load_model()
            logger.info("✅ Modelo MLP carregado")
        except Exception as e:
            logger.error(f"❌ Erro no modelo MLP: {e}")

        logger.info("✅ DIAGNÓSTICO CONCLUÍDO COM SUCESSO")
        return True

    except Exception as e:
        logger.error(f"❌ Erro durante diagnóstico: {e}")
        logger.error(traceback.format_exc())
        return False

    finally:
        try:
            mt5.shutdown()
            logger.info("MT5 desconectado")
        except:
            pass

def main():
    """Função principal do diagnóstico"""
    logger.info("DIAGNÓSTICO DO PROBLEMA NO TRADING_ENGINE")
    logger.info("=" * 60)

    success = diagnosticar_problema()

    logger.info("=" * 60)
    if success:
        logger.info("✅ DIAGNÓSTICO: Sistema funcionando corretamente")
        logger.info("O problema pode estar relacionado ao contexto específico de execução")
    else:
        logger.error("❌ DIAGNÓSTICO: Problemas identificados")

    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Diagnóstico interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro fatal no diagnóstico: {str(e)}")
        sys.exit(1)
