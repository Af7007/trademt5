"""
Testar lógica de sinais
"""

def test_signal_logic(rsi, price, sma_20, sma_50):
    """Testa a lógica de sinais"""
    signal = 'HOLD'
    confidence = 0.50
    
    print(f"\nTestando: RSI={rsi:.1f}, Price={price:.2f}, SMA20={sma_20:.2f}, SMA50={sma_50:.2f}")
    
    # Sinais fortes (alta confiança)
    if rsi < 30:
        signal = 'BUY'
        confidence = 0.85
        print(f"  → RSI < 30 → BUY 85%")
    elif rsi > 70:
        signal = 'SELL'
        confidence = 0.85
        print(f"  → RSI > 70 → SELL 85%")
    # Sinais médios baseados em tendência
    elif rsi < 40 and price > sma_20 and sma_20 > sma_50:
        signal = 'BUY'
        confidence = 0.70
        print(f"  → RSI < 40 + Tendência Alta → BUY 70%")
    elif rsi > 60 and price < sma_20 and sma_20 < sma_50:
        signal = 'SELL'
        confidence = 0.70
        print(f"  → RSI > 60 + Tendência Baixa → SELL 70%")
    # Sinais de tendência
    elif price > sma_20 > sma_50 and rsi > 50:
        signal = 'BUY'
        confidence = 0.65
        print(f"  → Tendência Alta + RSI > 50 → BUY 65%")
    elif price < sma_20 < sma_50 and rsi < 50:
        signal = 'SELL'
        confidence = 0.65
        print(f"  → Tendência Baixa + RSI < 50 → SELL 65%")
    else:
        print(f"  → Nenhuma condição atendida → HOLD 50%")
    
    print(f"  Resultado: {signal} {confidence*100:.0f}%")
    return signal, confidence

# Testar com os dados que você viu
print("="*80)
print("  TESTE DE LÓGICA DE SINAIS")
print("="*80)

# Caso 1: RSI 33.7 (do seu log)
test_signal_logic(33.7, 110782.81, 110836.70, 110800.00)

# Caso 2: RSI 75.1 (sobrecomprado)
test_signal_logic(75.1, 110885.04, 110820.51, 110800.00)

# Caso 3: RSI 64.7 (do seu log)
test_signal_logic(64.7, 110863.19, 110827.40, 110800.00)

# Caso 4: RSI 50.6 (neutro)
test_signal_logic(50.6, 110769.05, 110729.73, 110700.00)

print("\n" + "="*80)
