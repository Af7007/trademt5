import MetaTrader5 as mt5

# Inicializar MT5
mt5.initialize()

# Obter todos os símbolos
symbols = mt5.symbols_get()

print("Símbolos disponíveis com XAU ou GOLD:")
count = 0
for symbol in symbols:
    if 'XAU' in symbol.name or 'GOLD' in symbol.name:
        print(f"  {symbol.name}")
        count += 1
        if count >= 10:
            break

print(f"\nTotal encontrado: {count}")

# Verificar se XAUUSD existe especificamente
xauusd = mt5.symbol_info("XAUUSD")
if xauusd:
    print(f"XAUUSD encontrado: {xauusd.name}")
else:
    print("XAUUSD não encontrado")

mt5.shutdown()
