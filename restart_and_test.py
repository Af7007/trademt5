"""
Script para reiniciar o bot e executar o teste XAU
"""
import requests
import time
import subprocess
import sys

print("="*70)
print("  REINICIANDO BOT E EXECUTANDO TESTE XAU")
print("="*70)

# Passo 1: Tentar parar o bot
print("\n1. Parando bot...")
try:
    r = requests.post("http://localhost:5000/mlp/emergency-close", timeout=5)
    print(f"   Emergency close: {r.status_code}")
except:
    print("   Bot não estava rodando ou já parado")

time.sleep(2)

# Passo 2: Executar o teste
print("\n2. Executando teste XAU...")
print("-"*70)

# Executar o teste
result = subprocess.run([sys.executable, "test_xau_m1_rapido.py"], 
                       capture_output=False, 
                       text=True)

print("-"*70)
print(f"\n3. Teste finalizado com código: {result.returncode}")
