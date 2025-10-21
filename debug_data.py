import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()

# Teste exato igual ao trading_engine
symbol = 'XAUUSDc'
timeframe_mt5 = mt5.TIMEFRAME_M1
sequence_length = 60

print(f'Tentando obter dados para {symbol}...')
rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, sequence_length)

print(f'Rates: {rates}')
print(f'Rates is None: {rates is None}')
print(f'Len rates: {len(rates) if rates is not None else 0}')

if rates is None or len(rates) == 0:
    print(f"Não foi possível obter dados para {symbol}")
else:
    print(f'Dados obtidos com sucesso: {len(rates)} candles')

mt5.shutdown()
