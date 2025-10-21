"""
Script para abrir o Multi-Bot Manager
"""
import webbrowser

url = "http://localhost:5000/multi-bot-manager"

print("="*70)
print("  ABRINDO MULTI-BOT MANAGER")
print("="*70)
print(f"\nURL: {url}")
print("\n🤖 Sistema de Múltiplos Bots Simultâneos")
print("\nRecursos:")
print("  ✅ Criar múltiplos bots ao mesmo tempo")
print("  ✅ Cada bot opera um símbolo diferente")
print("  ✅ Controle individual de cada bot")
print("  ✅ Estatísticas consolidadas")
print("  ✅ Parada de emergência em todos")
print("\nAbrindo navegador...")

webbrowser.open(url)

print("\n✓ Navegador aberto!")
print("\nInstruções:")
print("  1. Use os templates ou configure manualmente")
print("  2. Clique em 'CRIAR E INICIAR BOT'")
print("  3. Repita para criar mais bots")
print("  4. Monitore todos em tempo real")
print("  5. Controle cada bot individualmente")
print("\n" + "="*70)
