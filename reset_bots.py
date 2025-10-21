"""
Reset completo - Deleta todos os bots
"""
import requests

print("="*80)
print("  RESET COMPLETO DE BOTS")
print("="*80)

# Buscar todos os bots
response = requests.get("http://localhost:5000/bots")
data = response.json()

if not data['success']:
    print(f"Erro: {data.get('error')}")
    exit()

bots = data['bots']
print(f"\nBots encontrados: {len(bots)}")

if len(bots) == 0:
    print("\nNenhum bot para deletar.")
    exit()

# Deletar cada bot
for bot in bots:
    bot_id = bot['bot_id']
    symbol = bot['config'].get('symbol', 'N/A')
    
    print(f"\nDeletando bot #{bot_id} ({symbol})...")
    
    response = requests.delete(f"http://localhost:5000/bots/{bot_id}/delete")
    result = response.json()
    
    if result['success']:
        print(f"  ✓ Bot #{bot_id} deletado")
    else:
        print(f"  ✗ Erro: {result.get('error')}")

print("\n" + "="*80)
print("  RESET CONCLUÍDO")
print("="*80)
print("\nAgora você pode criar bots novos que terão as threads de análise.")
print("\nPróximos passos:")
print("  1. Acesse: http://localhost:5000/bot-manager-pro")
print("  2. Clique 'Template BTC' → 'CRIAR E INICIAR BOT'")
print("  3. Clique 'Template XAU' → 'CRIAR E INICIAR BOT'")
print("  4. Aguarde 20 segundos")
print("  5. Execute: python check_threads.py")
