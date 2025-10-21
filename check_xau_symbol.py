import MetaTrader5 as mt5
import json

# Inicializar MT5
if not mt5.initialize():
    print("Falha ao inicializar MT5")
    exit()

# Verificar símbolo XAUUSDc
symbol = "XAUUSDc"
print(f"Verificando símbolo: {symbol}\n")

# Info do símbolo
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print(f"Símbolo {symbol} não encontrado!")
    print("\nTentando símbolos alternativos...")
    
    # Tentar variações
    for alt in ["XAUUSD", "XAU/USD", "GOLD", "GOLDc"]:
        info = mt5.symbol_info(alt)
        if info:
            print(f"  ✓ Encontrado: {alt}")
else:
    print(f"✓ Símbolo encontrado: {symbol}")
    print(f"\nDetalhes do símbolo:")
    print(f"  Visible: {symbol_info.visible}")
    print(f"  Selected: {symbol_info.select}")
    print(f"  Digits: {symbol_info.digits}")
    print(f"  Point: {symbol_info.point}")
    print(f"  Spread: {symbol_info.spread}")
    print(f"  Trade Mode: {symbol_info.trade_mode}")
    print(f"  Trade Stops Level: {symbol_info.trade_stops_level}")
    print(f"  Trade Freeze Level: {symbol_info.trade_freeze_level}")
    print(f"  Volume Min: {symbol_info.volume_min}")
    print(f"  Volume Max: {symbol_info.volume_max}")
    print(f"  Volume Step: {symbol_info.volume_step}")
    print(f"  Contract Size: {symbol_info.trade_contract_size}")
    print(f"  Tick Value: {symbol_info.trade_tick_value}")
    print(f"  Tick Size: {symbol_info.trade_tick_size}")
    
    # Tentar selecionar o símbolo
    if not symbol_info.visible:
        print(f"\n⚠ Símbolo não visível, tentando selecionar...")
        if mt5.symbol_select(symbol, True):
            print(f"  ✓ Símbolo selecionado com sucesso!")
        else:
            print(f"  ✗ Falha ao selecionar símbolo")
    
    # Obter tick atual
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"\nTick Atual:")
        print(f"  Bid: {tick.bid}")
        print(f"  Ask: {tick.ask}")
        print(f"  Last: {tick.last}")
        print(f"  Volume: {tick.volume}")
        
        # Calcular valores válidos de SL/TP
        stops_level = symbol_info.trade_stops_level
        point = symbol_info.point
        
        print(f"\nNíveis de Stop:")
        print(f"  Stops Level: {stops_level} pontos")
        print(f"  Distância mínima: {stops_level * point} (em preço)")
        
        # Exemplo de ordem BUY
        price = tick.ask
        min_sl = price - (stops_level * point)
        min_tp = price + (stops_level * point)
        
        print(f"\nExemplo para ordem BUY ao preço {price}:")
        print(f"  SL mínimo: {min_sl}")
        print(f"  TP mínimo: {min_tp}")
        
        # Calcular TP/SL para $0.50
        tick_value = symbol_info.trade_tick_value
        volume = 0.01  # 0.01 lote
        
        # Para lucro de $0.50 com 0.01 lote
        # profit = (price_diff / point) * tick_value * volume
        # 0.50 = (tp_distance / point) * tick_value * volume
        # tp_distance = (0.50 * point) / (tick_value * volume)
        
        tp_distance = (0.50 * point) / (tick_value * volume)
        tp_price = price + tp_distance
        
        print(f"\nPara lucro de $0.50 com volume {volume}:")
        print(f"  TP deve estar em: {tp_price}")
        print(f"  Distância: {tp_distance} ({tp_distance/point} pontos)")

mt5.shutdown()
