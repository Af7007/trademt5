import MetaTrader5 as mt5

# Inicializar MT5
if not mt5.initialize():
    print("Falha ao inicializar MT5")
    exit()

# Verificar símbolo BTCUSDc
symbol = "BTCUSDc"
print(f"Verificando símbolo: {symbol}\n")

# Info do símbolo
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print(f"Símbolo {symbol} não encontrado!")
else:
    print(f"✓ Símbolo encontrado: {symbol}")
    print(f"\nDetalhes do símbolo:")
    print(f"  Visible: {symbol_info.visible}")
    print(f"  Selected: {symbol_info.select}")
    print(f"  Digits: {symbol_info.digits}")
    print(f"  Point: {symbol_info.point}")
    print(f"  Spread: {symbol_info.spread}")
    print(f"  Trade Stops Level: {symbol_info.trade_stops_level}")
    print(f"  Volume Min: {symbol_info.volume_min}")
    print(f"  Volume Max: {symbol_info.volume_max}")
    print(f"  Contract Size: {symbol_info.trade_contract_size}")
    print(f"  Tick Value: {symbol_info.trade_tick_value}")
    print(f"  Tick Size: {symbol_info.trade_tick_size}")
    
    # Obter tick atual
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"\nTick Atual:")
        print(f"  Bid: {tick.bid}")
        print(f"  Ask: {tick.ask}")
        print(f"  Last: {tick.last}")
        print(f"  Volume: {tick.volume}")
        
        # Calcular TP/SL para $0.50
        tick_value = symbol_info.trade_tick_value
        point = symbol_info.point
        volume = 0.01  # 0.01 lote
        
        price = tick.ask
        
        # Para lucro de $0.50 com 0.01 lote
        # profit = (price_diff / point) * tick_value * volume
        # 0.50 = (tp_distance / point) * tick_value * volume
        # tp_distance = (0.50 * point) / (tick_value * volume)
        
        tp_distance = (0.50 * point) / (tick_value * volume)
        tp_price = price + tp_distance
        sl_distance = (1.00 * point) / (tick_value * volume)
        sl_price = price - sl_distance
        
        print(f"\nPara lucro de $0.50 com volume {volume}:")
        print(f"  Preço atual: {price}")
        print(f"  TP deve estar em: {tp_price}")
        print(f"  TP distância: {tp_distance} ({tp_distance/point} pontos)")
        print(f"  SL deve estar em: {sl_price}")
        print(f"  SL distância: {sl_distance} ({sl_distance/point} pontos)")

mt5.shutdown()
