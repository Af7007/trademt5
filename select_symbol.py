import MetaTrader5 as mt5

mt5.initialize()

print('Verificando seleção do símbolo...')
selected = mt5.symbol_select('XAUUSDc', True)
print(f'Symbol select result: {selected}')

info = mt5.symbol_info('XAUUSDc')
print(f'Symbol info: {info}')

mt5.shutdown()
