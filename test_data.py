import MetaTrader5 as mt5

mt5.initialize()

rates = mt5.copy_rates_from_pos('XAUUSDc', mt5.TIMEFRAME_M1, 0, 10)
print(f'Rates: {rates}')
print(f'Len: {len(rates) if rates is not None else 0}')

mt5.shutdown()
