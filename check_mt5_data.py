"""
Verificar se MT5 está retornando dados de mercado
"""
import MetaTrader5 as mt5
from datetime import datetime

# Inicializar MT5
if not mt5.initialize():
    print("Falha ao inicializar MT5")
    exit()

print("="*80)
print("  VERIFICAÇÃO DE DADOS DO MT5")
print("="*80)

symbols = ["BTCUSDc", "XAUUSDc", "EURUSD", "GBPUSD"]

for symbol in symbols:
    print(f"\n{'='*80}")
    print(f"  {symbol}")
    print(f"{'='*80}")
    
    # Selecionar símbolo
    mt5.symbol_select(symbol, True)
    
    # Obter tick
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"Tick:")
        print(f"  Bid: {tick.bid}")
        print(f"  Ask: {tick.ask}")
        print(f"  Last: {tick.last}")
        print(f"  Time: {datetime.fromtimestamp(tick.time)}")
    else:
        print(f"✗ Sem tick disponível")
    
    # Obter barras M1
    import pandas as pd
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
    
    if rates is not None and len(rates) > 0:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        print(f"\nBarras M1 (últimas 5):")
        for i in range(min(5, len(df))):
            row = df.iloc[-(i+1)]
            print(f"  {row['time']} | O: {row['open']:.2f} | H: {row['high']:.2f} | L: {row['low']:.2f} | C: {row['close']:.2f} | V: {row['tick_volume']}")
        
        # Calcular RSI simples
        closes = df['close'].values
        if len(closes) >= 14:
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            avg_gain = sum(gains[-14:]) / 14
            avg_loss = sum(losses[-14:]) / 14
            
            if avg_loss > 0:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                print(f"\nRSI (14): {rsi:.2f}")
            else:
                print(f"\nRSI: Sem perdas recentes")
        
        # Calcular SMA
        if len(closes) >= 20:
            sma20 = sum(closes[-20:]) / 20
            print(f"SMA(20): {sma20:.2f}")
        
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            print(f"SMA(50): {sma50:.2f}")
    else:
        print(f"✗ Sem dados de barras disponíveis")

mt5.shutdown()

print("\n" + "="*80)
print("  CONCLUSÃO")
print("="*80)
print("\nSe os dados acima estão zerados ou não disponíveis:")
print("  1. O mercado pode estar fechado")
print("  2. O símbolo não está selecionado no Market Watch")
print("  3. Há problema de conexão com o broker")
print("\nSe os dados estão OK mas as análises ficam em HOLD:")
print("  1. O modelo MLP não está treinado")
print("  2. O threshold de confiança está muito alto")
print("  3. Os indicadores não estão sendo calculados corretamente")
