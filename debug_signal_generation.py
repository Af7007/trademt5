"""
Debug completo da geração de sinais
"""
import MetaTrader5 as mt5
import pandas as pd

print("="*80)
print("  DEBUG COMPLETO - GERAÇÃO DE SINAIS")
print("="*80)

# Inicializar MT5
if not mt5.initialize():
    print("Erro ao inicializar MT5")
    exit()

symbol = "BTCUSDc"
print(f"\n1. Coletando dados de {symbol}...")

# Obter dados
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)

if rates is None or len(rates) == 0:
    print("✗ Sem dados!")
    exit()

print(f"✓ {len(rates)} candles obtidos")

# Converter para DataFrame
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

print(f"\n2. Últimos 5 candles:")
print(df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].tail())

# Calcular indicadores
close = df['close'].values

print(f"\n3. Calculando indicadores...")

# RSI
deltas = [close[i] - close[i-1] for i in range(1, len(close))]
gains = [d if d > 0 else 0 for d in deltas]
losses = [-d if d < 0 else 0 for d in deltas]
avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 0
avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 0
rsi = 100 - (100 / (1 + (avg_gain / avg_loss))) if avg_loss > 0 else 50

# SMA
sma_20 = sum(close[-20:]) / 20 if len(close) >= 20 else close[-1]
sma_50 = sum(close[-50:]) / 50 if len(close) >= 50 else close[-1]

price = close[-1]

print(f"  RSI (14): {rsi:.2f}")
print(f"  SMA (20): {sma_20:.2f}")
print(f"  SMA (50): {sma_50:.2f}")
print(f"  Price: {price:.2f}")

# Determinar trend
if sma_20 > sma_50:
    trend = 'BULLISH'
elif sma_20 < sma_50:
    trend = 'BEARISH'
else:
    trend = 'NEUTRAL'

print(f"  Trend: {trend}")

print(f"\n4. Aplicando lógica de sinais...")

signal = 'HOLD'
confidence = 0.50
reason = "Nenhuma condição atendida"

# Sinais fortes (alta confiança)
if rsi < 30:
    signal = 'BUY'
    confidence = 0.85
    reason = "RSI < 30 (sobrevendido forte)"
elif rsi > 70:
    signal = 'SELL'
    confidence = 0.85
    reason = "RSI > 70 (sobrecomprado forte)"
# Sinais médios baseados em RSI
elif rsi < 40:
    signal = 'BUY'
    confidence = 0.70
    reason = "RSI < 40"
elif rsi > 60:
    signal = 'SELL'
    confidence = 0.70
    reason = "RSI > 60"
# Sinais de tendência
elif price > sma_20 > sma_50 and rsi > 50:
    signal = 'BUY'
    confidence = 0.65
    reason = "Tendência Alta + RSI > 50"
elif price < sma_20 < sma_50 and rsi < 50:
    signal = 'SELL'
    confidence = 0.65
    reason = "Tendência Baixa + RSI < 50"

print(f"\n5. RESULTADO:")
print(f"  Sinal: {signal}")
print(f"  Confiança: {confidence*100:.0f}%")
print(f"  Razão: {reason}")

print(f"\n6. Verificando condições:")
print(f"  rsi < 30? {rsi < 30} (rsi={rsi:.2f})")
print(f"  rsi > 70? {rsi > 70} (rsi={rsi:.2f})")
print(f"  rsi < 40? {rsi < 40} (rsi={rsi:.2f})")
print(f"  rsi > 60? {rsi > 60} (rsi={rsi:.2f})")
print(f"  price > sma_20 > sma_50? {price > sma_20 > sma_50}")
print(f"    price={price:.2f}, sma_20={sma_20:.2f}, sma_50={sma_50:.2f}")
print(f"  rsi > 50? {rsi > 50} (rsi={rsi:.2f})")

mt5.shutdown()

print("\n" + "="*80)
print("  FIM DO DEBUG")
print("="*80)
