"""
Teste simples: executar ordem XAU sem SL/TP para verificar se o problema é nos stops
"""
import MetaTrader5 as mt5
import time

# Inicializar MT5
if not mt5.initialize():
    print("Falha ao inicializar MT5")
    exit()

symbol = "XAUUSDc"
volume = 0.01

# Selecionar símbolo
mt5.symbol_select(symbol, True)

# Obter preço atual
tick = mt5.symbol_info_tick(symbol)
if not tick:
    print(f"Falha ao obter tick de {symbol}")
    mt5.shutdown()
    exit()

print(f"Preço atual: Bid={tick.bid}, Ask={tick.ask}")

# Preparar ordem BUY SEM SL/TP
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "magic": 123456,
    "comment": "Teste XAU sem SL/TP"
}

print(f"\nEnviando ordem BUY {volume} lote de {symbol}...")
print(f"Request: {request}")

# Enviar ordem
result = mt5.order_send(request)

print(f"\nResultado:")
print(f"  Retcode: {result.retcode}")
print(f"  Comment: {result.comment}")

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"  ✓ SUCESSO! Ticket: {result.order}")
    print(f"  Volume: {result.volume}")
    print(f"  Price: {result.price}")
    
    # Aguardar um pouco
    print("\nAguardando 5 segundos...")
    time.sleep(5)
    
    # Fechar posição
    print("\nFechando posição...")
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        pos = positions[0]
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "position": pos.ticket,
            "magic": 123456,
            "comment": "Fechamento teste"
        }
        
        close_result = mt5.order_send(close_request)
        print(f"Fechamento - Retcode: {close_result.retcode}, Comment: {close_result.comment}")
        
        if close_result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✓ Posição fechada com sucesso!")
            print(f"  Profit: ${close_result.profit if hasattr(close_result, 'profit') else 'N/A'}")
else:
    print(f"  ✗ FALHA: {result.comment}")

mt5.shutdown()
