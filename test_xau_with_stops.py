"""
Teste: executar ordem XAU COM SL/TP para verificar valores corretos
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

# Obter info do símbolo
symbol_info = mt5.symbol_info(symbol)
print(f"Símbolo: {symbol}")
print(f"  Digits: {symbol_info.digits}")
print(f"  Point: {symbol_info.point}")
print(f"  Stops Level: {symbol_info.trade_stops_level}")

# Obter preço atual
tick = mt5.symbol_info_tick(symbol)
if not tick:
    print(f"Falha ao obter tick de {symbol}")
    mt5.shutdown()
    exit()

price = tick.ask
print(f"\nPreço atual: Bid={tick.bid}, Ask={tick.ask}")

# Calcular SL/TP para $0.50 de lucro
# tick_value = 0.1 (com 1 lote), então com 0.01 lote = 0.001 por ponto
# Para $0.50: precisa de 500 pontos = 0.5 em preço
tp_distance = 0.5  # 500 pontos
sl_distance = 1.0  # 1000 pontos

tp = round(price + tp_distance, symbol_info.digits)
sl = round(price - sl_distance, symbol_info.digits)

print(f"\nCálculo de SL/TP:")
print(f"  Preço entrada: {price}")
print(f"  TP: {tp} (distância: {tp_distance})")
print(f"  SL: {sl} (distância: {sl_distance})")

# Preparar ordem BUY COM SL/TP
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "sl": sl,
    "tp": tp,
    "magic": 123456,
    "comment": "Teste XAU com SL/TP"
}

print(f"\nEnviando ordem BUY {volume} lote de {symbol}...")
print(f"Request completo: {request}")

# Enviar ordem
result = mt5.order_send(request)

print(f"\nResultado:")
print(f"  Retcode: {result.retcode}")
print(f"  Comment: {result.comment}")

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"  ✓ SUCESSO! Ticket: {result.order}")
    print(f"  Volume: {result.volume}")
    print(f"  Price: {result.price}")
    
    # Verificar posição
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        pos = positions[0]
        print(f"\nPosição aberta:")
        print(f"  Ticket: {pos.ticket}")
        print(f"  Price: {pos.price_open}")
        print(f"  SL: {pos.sl}")
        print(f"  TP: {pos.tp}")
        print(f"  Profit atual: ${pos.profit:.2f}")
        
        # Aguardar um pouco
        print("\nAguardando 5 segundos para monitorar...")
        time.sleep(5)
        
        # Verificar novamente
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            pos = positions[0]
            print(f"Profit após 5s: ${pos.profit:.2f}")
            
            # Fechar manualmente
            print("\nFechando posição manualmente...")
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL,
                "position": pos.ticket,
                "magic": 123456,
                "comment": "Fechamento manual"
            }
            
            close_result = mt5.order_send(close_request)
            if close_result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✓ Posição fechada!")
        else:
            print("Posição já foi fechada automaticamente (TP/SL atingido)")
else:
    print(f"  ✗ FALHA: {result.comment}")
    print(f"  Retcode detalhado: {result.retcode}")
    
    # Códigos de erro comuns
    if result.retcode == 10016:
        print("  Erro: Invalid stops (SL/TP inválidos)")
    elif result.retcode == 10014:
        print("  Erro: Invalid volume")
    elif result.retcode == 10015:
        print("  Erro: Invalid price")

mt5.shutdown()
