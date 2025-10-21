"""
Testar se o módulo está sendo importado corretamente
"""
import sys
import importlib

# Remover do cache se existir
if 'services.bot_manager_service' in sys.modules:
    del sys.modules['services.bot_manager_service']

# Importar
from services.bot_manager_service import BotInstance

# Verificar código
import inspect
source = inspect.getsource(BotInstance._analysis_loop)

print("="*80)
print("  VERIFICAÇÃO DE CÓDIGO")
print("="*80)

# Procurar pela linha específica
if "elif rsi < 40:" in source:
    print("\n✓ CÓDIGO NOVO ENCONTRADO!")
    print("  Linha: elif rsi < 40:")
else:
    print("\n✗ CÓDIGO ANTIGO!")
    print("  Não encontrou: elif rsi < 40:")

if "elif rsi < 40 and close[-1] > sma_20" in source:
    print("\n✗ CÓDIGO ANTIGO AINDA PRESENTE!")
    print("  Encontrou código antigo com condição complexa")

print("\n" + "="*80)
print("Primeiras linhas da lógica de sinais:")
print("="*80)
for line in source.split('\n')[40:60]:
    if 'rsi' in line.lower() or 'signal' in line.lower():
        print(line)
