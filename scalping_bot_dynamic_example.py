#!/usr/bin/env python3
"""
Exemplo de uso do Scalping Bot com gerenciamento de risco dinâmico
"""

import MetaTrader5 as mt5
from scalping_bot import ScalpingBot

def main():
    """Demonstra o uso do bot com diferentes configurações de risco"""

    print("SCALPING BOT - GERENCIAMENTO DE RISCO DINAMICO")
    print("=" * 60)

    # Inicializar MT5
    if not mt5.initialize():
        print("ERRO: Erro ao inicializar MT5")
        return

    print("OK: MT5 inicializado com sucesso")

    # === EXEMPLO 1: Modo Dinâmico (Recomendado) ===
    print("\nEXEMPLO 1: Modo Dinamico (20% banca | $0.50 lucro)")
    print("-" * 50)

    bot_dynamic = ScalpingBot(
        symbol="BTCUSDc",
        timeframe=mt5.TIMEFRAME_M5,
        confidence_threshold=85,
        volume=0.01,
        use_dynamic_risk=True  # Ativa gerenciamento dinâmico
    )

    # Executar uma verificação única
    result = bot_dynamic.run_once()
    print(f"Resultado: {result}")

    # === EXEMPLO 2: Modo Percentual (Tradicional) ===
    print("\nEXEMPLO 2: Modo Percentual (0.5% SL | 0.3% TP)")
    print("-" * 50)

    bot_percentage = ScalpingBot(
        symbol="BTCUSDc",
        timeframe=mt5.TIMEFRAME_M5,
        confidence_threshold=85,
        volume=0.01,
        use_dynamic_risk=False  # Desativa gerenciamento dinâmico
    )

    # Executar uma verificação única
    result = bot_percentage.run_once()
    print(f"Resultado: {result}")

    # === EXEMPLO 3: Configurações Customizadas ===
    print("\nEXEMPLO 3: Configuracoes Customizadas")
    print("-" * 50)

    bot_custom = ScalpingBot(
        symbol="BTCUSDc",
        timeframe=mt5.TIMEFRAME_M1,  # Timeframe menor
        confidence_threshold=90,     # Confiança mais alta
        volume=0.02,                 # Volume maior
        use_dynamic_risk=True
    )

    # Obter estatísticas
    stats = bot_custom.get_stats()
    print("Configurações do bot:")
    print(f"  - Símbolo: {stats['symbol']}")
    print(f"  - Timeframe: M1")
    print(f"  - Confiança mínima: {stats['confidence_threshold']}%")
    print(f"  - Volume: {bot_custom.volume} lotes")
    print(f"  - Modo: {'Dinâmico' if bot_custom.use_dynamic_risk else 'Percentual'}")

    # === DEMONSTRAÇÃO DE CÁLCULO DE RISCO ===
    print("\nDEMONSTRACAO DE CALCULO DE RISCO")
    print("-" * 50)

    # Simular cálculo de SL/TP dinâmico
    current_price = 107000.0

    # Calcular risco dinâmico
    sl_dynamic, tp_dynamic = bot_dynamic.calculate_dynamic_sl_tp(current_price, "BUY")
    print(f"Preço atual: ${current_price:.2f}")
    print(f"SL Dinâmico: ${sl_dynamic:.2f}")
    print(f"TP Dinâmico: ${tp_dynamic:.2f}")

    # Calcular risco percentual
    sl_pct, tp_pct = bot_dynamic.calculate_percentage_sl_tp(current_price, "BUY")
    print(f"SL Percentual: ${sl_pct:.2f}")
    print(f"TP Percentual: ${tp_pct:.2f}")

    print("\nDemonstracao concluida!")
    print("\nPara iniciar o bot em modo contínuo:")
    print("  bot.run(interval=60)  # Verificar a cada 60 segundos")

    # Finalizar MT5
    mt5.shutdown()
    print("MT5 desconectado")

if __name__ == "__main__":
    main()
