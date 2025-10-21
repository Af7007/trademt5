import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()

# Teste completo igual ao trading_engine
symbol = 'XAUUSDc'
timeframe_mt5 = mt5.TIMEFRAME_M1
sequence_length = 60

print(f'Obtendo dados para {symbol}...')
rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, sequence_length)

if rates is None or len(rates) == 0:
    print(f'Não foi possível obter dados para {symbol}')
else:
    print(f'Dados obtidos: {len(rates)} candles')
    market_data = pd.DataFrame(rates)
    market_data['time'] = pd.to_datetime(market_data['time'], unit='s')
    market_data = market_data[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    print(f'DataFrame criado: {len(market_data)} linhas')
    print(f'Última linha: {market_data.iloc[-1].to_dict()}')

mt5.shutdown()
