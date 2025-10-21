import MetaTrader5 as mt5
from datetime import datetime

# Inicializar MT5
if not mt5.initialize():
    print("Falha ao inicializar MT5")
    exit()

print("="*70)
print("  VERIFICAÇÃO DE MERCADOS ABERTOS")
print("="*70)
print(f"\nHora atual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Lista de símbolos para verificar
symbols = ["BTCUSDc", "XAUUSDc", "EURUSD", "GBPUSD", "USDJPY"]

print("Verificando status dos mercados:\n")

for symbol in symbols:
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        tick = mt5.symbol_info_tick(symbol)
        
        # Verificar se o mercado está aberto
        # Se o spread é muito alto ou volume é 0, geralmente está fechado
        is_open = tick and tick.bid > 0 and tick.ask > 0
        
        status = "✓ ABERTO" if is_open else "✗ FECHADO"
        
        print(f"{symbol:12} - {status}")
        if is_open:
            print(f"  Bid: {tick.bid}, Ask: {tick.ask}, Spread: {tick.ask - tick.bid}")
        else:
            print(f"  Mercado fechado ou sem cotação")
    else:
        print(f"{symbol:12} - Não encontrado")
    print()

# Informações da conta
account_info = mt5.account_info()
if account_info:
    print("\nInformações da Conta:")
    print(f"  Servidor: {account_info.server}")
    print(f"  Trade Mode: {account_info.trade_mode}")
    print(f"  Balance: ${account_info.balance:.2f}")
    print(f"  Equity: ${account_info.equity:.2f}")

mt5.shutdown()
