"""
Teste de intercalação de análises de múltiplos símbolos
"""
import requests
import json

print("="*80)
print("  TESTE DE INTERCALAÇÃO DE ANÁLISES")
print("="*80)

# 1. Verificar bots ativos
print("\n1. Verificando bots ativos...")
response = requests.get("http://localhost:5000/bots")
data = response.json()

if data['success']:
    bots = data['bots']
    print(f"   Total de bots: {len(bots)}")
    
    active_bots = [b for b in bots if b['is_running']]
    print(f"   Bots ativos: {len(active_bots)}")
    
    for bot in active_bots:
        symbol = bot['config'].get('symbol', 'N/A')
        print(f"   - Bot #{bot['bot_id']}: {symbol}")
    
    if len(active_bots) < 2:
        print("\n   ⚠ AVISO: Você precisa de pelo menos 2 bots ativos para ver intercalação!")
        print("   Crie e inicie bots para BTC e XAU")
else:
    print(f"   ✗ Erro: {data.get('error')}")
    exit()

# 2. Buscar análises
print("\n2. Buscando análises...")
response = requests.get("http://localhost:5000/bots/analyses")
data = response.json()

if data['success']:
    analyses = data['analyses']
    print(f"   Total de análises: {len(analyses)}")
    
    if len(analyses) == 0:
        print("   ⚠ Nenhuma análise disponível ainda")
        exit()
    
    # Contar por símbolo
    symbols_count = {}
    for a in analyses:
        sym = a.get('symbol', 'N/A')
        symbols_count[sym] = symbols_count.get(sym, 0) + 1
    
    print("\n   Análises por símbolo:")
    for sym, count in symbols_count.items():
        print(f"   - {sym}: {count} análises")
    
    # Mostrar primeiras 10 com timestamps
    print("\n3. Primeiras 10 análises (ordem cronológica):")
    print("   " + "-"*76)
    
    for i, analysis in enumerate(analyses[:10]):
        timestamp = analysis.get('timestamp', 'N/A')
        symbol = analysis.get('symbol', 'N/A')
        signal = analysis.get('signal', 'N/A')
        confidence = analysis.get('confidence', 0) * 100
        
        print(f"   {i+1:2}. {timestamp} | {symbol:10} | {signal:4} | {confidence:5.1f}%")
    
    # Verificar intercalação
    print("\n4. Verificando intercalação...")
    
    if len(symbols_count) < 2:
        print("   ⚠ Apenas 1 símbolo encontrado - não há intercalação")
    else:
        # Verificar se símbolos estão intercalados
        symbols_sequence = [a.get('symbol') for a in analyses[:10]]
        
        # Contar transições entre símbolos
        transitions = 0
        for i in range(len(symbols_sequence) - 1):
            if symbols_sequence[i] != symbols_sequence[i+1]:
                transitions += 1
        
        if transitions > 0:
            print(f"   ✓ INTERCALAÇÃO DETECTADA! {transitions} transições entre símbolos")
        else:
            print(f"   ✗ SEM INTERCALAÇÃO - Todas análises do mesmo símbolo")
            print(f"   Sequência: {' -> '.join(symbols_sequence[:5])}")
    
    # Verificar sinais
    print("\n5. Distribuição de sinais:")
    signals_count = {}
    for a in analyses:
        sig = a.get('signal', 'N/A')
        signals_count[sig] = signals_count.get(sig, 0) + 1
    
    total = len(analyses)
    for sig, count in signals_count.items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"   {sig:4}: {count:3} ({pct:5.1f}%)")
    
    if signals_count.get('HOLD', 0) == total:
        print("\n   ⚠ TODOS OS SINAIS SÃO HOLD!")
        print("   Isso pode indicar:")
        print("   - Modelo muito conservador")
        print("   - Threshold de confiança muito alto")
        print("   - Mercado em consolidação")

else:
    print(f"   ✗ Erro: {data.get('error')}")

print("\n" + "="*80)
