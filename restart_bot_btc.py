"""
Script para reiniciar completamente o bot e testar BTC
"""
import requests
import time
import sys

print("="*70)
print("  REINICIANDO BOT PARA BTC")
print("="*70)

# Passo 1: Emergency close
print("\n1. Fechando todas as posições e parando bot...")
try:
    r = requests.post("http://localhost:5000/mlp/emergency-close", timeout=10)
    print(f"   Emergency close: {r.status_code}")
    if r.status_code == 200:
        result = r.json()
        print(f"   Response: {result}")
except Exception as e:
    print(f"   Erro: {e}")

time.sleep(3)

# Passo 2: Verificar se o bot parou
print("\n2. Verificando status...")
try:
    r = requests.get("http://localhost:5000/mlp/status", timeout=5)
    if r.status_code == 200:
        status = r.json()
        print(f"   Bot running: {status.get('is_running', False)}")
        print(f"   MT5 connected: {status.get('mt5_connected', False)}")
except Exception as e:
    print(f"   Erro: {e}")

time.sleep(2)

print("\n3. Aguarde 5 segundos antes de executar o teste...")
print("   Isso garante que o bot reinicie completamente com a nova configuração")
time.sleep(5)

print("\n4. Executando teste BTC...")
print("="*70)
print()

# Executar o teste
import subprocess
result = subprocess.run([sys.executable, "test_btc_m1_rapido.py"])

print()
print("="*70)
print(f"Teste finalizado com código: {result.returncode}")
print("="*70)
