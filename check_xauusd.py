import MetaTrader5 as mt5

mt5.initialize()

# Verificar informações do símbolo
symbol_info = mt5.symbol_info('XAUUSDc')
print(f'XAUUSDc info: {symbol_info}')

if symbol_info:
    print(f'Nome: {symbol_info.name}')
    print(f'Visível: {symbol_info.visible}')
    print(f'Dígitos: {symbol_info.digits}')
    print(f'Volume mínimo: {symbol_info.volume_min}')
    print(f'Volume máximo: {symbol_info.volume_max}')
    print(f'Tick value: {symbol_info.trade_tick_value}')
    print(f'Contract size: {symbol_info.trade_contract_size}')
    print(f'Point: {symbol_info.point}')

    # Tentar obter dados históricos
    rates = mt5.copy_rates_from_pos('XAUUSDc', mt5.TIMEFRAME_M1, 0, 10)
    if rates is not None:
        print(f'Dados históricos obtidos: {len(rates)}')
        if len(rates) > 0:
            # Converter para dicionário para acessar os campos
            last_rate = rates[-1]
            print(f'Último preço (close): {last_rate["close"]}')
            print(f'Último preço (open): {last_rate["open"]}')
            print(f'Último preço (high): {last_rate["high"]}')
            print(f'Último preço (low): {last_rate["low"]}')
            print(f'Volume: {last_rate["tick_volume"]}')
        else:
            print('Dados históricos: Array vazio')
    else:
        print('Dados históricos: Nenhum dado obtido')

mt5.shutdown()
