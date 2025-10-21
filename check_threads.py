"""
Verificar threads de análise dos bots
"""
import requests
import time

print("="*80)
print("  VERIFICAÇÃO DE THREADS DE ANÁLISE")
print("="*80)

# Buscar bots
response = requests.get("http://localhost:5000/bots")
data = response.json()

if not data['success']:
    print(f"Erro: {data.get('error')}")
    exit()

bots = data['bots']
active_bots = [b for b in bots if b['is_running']]

print(f"\nBots ativos: {len(active_bots)}")
for bot in active_bots:
    print(f"  - Bot #{bot['bot_id']}: {bot['config'].get('symbol')}")

# Aguardar 30 segundos e verificar se análises foram geradas
print("\nAguardando 30 segundos para verificar geração de análises...")
print("(As threads devem gerar análises a cada 10 segundos)")

# Contar análises antes
response = requests.get("http://localhost:5000/bots/analyses")
data_before = response.json()
count_before = len(data_before.get('analyses', []))

print(f"\nAnálises antes: {count_before}")

# Aguardar
for i in range(30, 0, -1):
    print(f"\r  Aguardando... {i}s  ", end='', flush=True)
    time.sleep(1)

print("\n")

# Contar análises depois
response = requests.get("http://localhost:5000/bots/analyses")
data_after = response.json()
count_after = len(data_after.get('analyses', []))

print(f"Análises depois: {count_after}")
print(f"Novas análises: {count_after - count_before}")

if count_after > count_before:
    print("\n✓ Threads estão gerando análises!")
    
    # Verificar quais símbolos geraram análises
    analyses = data_after.get('analyses', [])
    symbols_new = {}
    
    for analysis in analyses[:count_after - count_before]:
        sym = analysis.get('symbol')
        symbols_new[sym] = symbols_new.get(sym, 0) + 1
    
    print("\nNovas análises por símbolo:")
    for sym, count in symbols_new.items():
        print(f"  {sym}: {count} análises")
else:
    print("\n✗ NENHUMA ANÁLISE NOVA GERADA!")
    print("\nPossíveis causas:")
    print("  1. Threads não estão rodando")
    print("  2. Erro no código de análise")
    print("  3. MT5 não está retornando dados")
    print("\nVerifique os logs do servidor Flask")

print("\n" + "="*80)
