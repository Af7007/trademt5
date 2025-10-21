"""
Diagnosticar por que trades não estão sendo executados
"""
import requests
import json

print("="*80)
print("  DIAGNÓSTICO DE TRADING AUTOMÁTICO")
print("="*80)

# Obter bots
response = requests.get("http://localhost:5000/bots")
data = response.json()

if not data.get('bots'):
    print("\n✗ Nenhum bot ativo!")
    exit()

bots = data['bots']
print(f"\n✓ {len(bots)} bot(s) encontrado(s)\n")

for bot in bots:
    bot_id = bot['bot_id']
    config = bot.get('config', {})
    
    print(f"Bot #{bot_id[:8]}")
    print(f"  Symbol: {config.get('symbol', 'N/A')}")
    print(f"  Running: {bot.get('is_running', False)}")
    print(f"  Positions: {bot.get('positions_count', 0)}")
    
    # Verificar configuração de trading
    trading = config.get('trading', {})
    
    print(f"\n  📊 CONFIGURAÇÃO DE TRADING:")
    print(f"    enabled: {trading.get('enabled', False)}")
    print(f"    auto_execute: {trading.get('auto_execute', False)}")
    
    if not trading.get('auto_execute', False):
        print(f"    ⚠️  AUTO_EXECUTE ESTÁ DESABILITADO!")
        print(f"    ⚠️  Para ativar, edite o bot e mude 'auto_execute' para true")
    
    # Verificar configuração de sinais
    signals = config.get('signals', {})
    print(f"\n  📈 CONFIGURAÇÃO DE SINAIS:")
    print(f"    min_confidence: {signals.get('min_confidence', 0.65)}")
    
    # Verificar parâmetros básicos
    print(f"\n  💰 PARÂMETROS:")
    print(f"    lot_size: {config.get('lot_size', 0.01)}")
    print(f"    take_profit: {config.get('take_profit', 5000)}")
    print(f"    stop_loss: {config.get('stop_loss', 10000)}")
    print(f"    max_positions: {config.get('max_positions', 1)}")
    
    print("\n" + "-"*80)

print("\n" + "="*80)
print("  RECOMENDAÇÕES")
print("="*80)

print("""
Para ATIVAR trading automático:

1. Clique em "CONFIG" no bot
2. Encontre a seção "trading"
3. Mude "auto_execute" de false para true
4. Copie o JSON completo
5. Delete o bot
6. Cole o JSON no campo de configuração
7. Clique "CRIAR E INICIAR BOT"

OU use este JSON como exemplo:
""")

example = {
    "symbol": "BTCUSDc",
    "lot_size": 0.01,
    "take_profit": 5000,
    "stop_loss": 10000,
    "max_positions": 1,
    "trading": {
        "enabled": True,
        "auto_execute": True
    },
    "signals": {
        "min_confidence": 0.65
    }
}

print(json.dumps(example, indent=2))

print("\n" + "="*80)
