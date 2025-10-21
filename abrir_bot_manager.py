"""
Script simples para abrir o Bot Manager
"""
import webbrowser
import time

url = "http://localhost:5000/bot-manager"

print("="*70)
print("  ABRINDO BOT MANAGER")
print("="*70)
print(f"\nURL: {url}")
print("\nAbrindo navegador...")

webbrowser.open(url)

print("\n✓ Navegador aberto!")
print("\nO Bot Manager está pronto para uso.")
print("\nInstruções:")
print("  1. Use os templates BTC ou XAU")
print("  2. Clique em 'INICIAR BOT'")
print("  3. Monitore em tempo real")
print("  4. Use 'PARAR BOT' quando necessário")
print("\n" + "="*70)
