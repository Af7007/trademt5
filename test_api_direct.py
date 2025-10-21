"""
Teste direto das APIs para diagnosticar o problema
"""
import requests
import json
import time

FLASK_URL = "http://localhost:5000"

def test_api(method, endpoint, data=None, description=""):
    """Testa um endpoint da API"""
    url = f"{FLASK_URL}{endpoint}"
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}")
    print(f"Método: {method}")
    print(f"URL: {url}")
    if data:
        print(f"Payload: {json.dumps(data, indent=2)}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response:")
            print(json.dumps(result, indent=2))
            return result
        except:
            print(f"Response (text): {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"ERRO: {e}")
        return None

print("="*70)
print("  TESTE DIRETO DAS APIs - DIAGNÓSTICO")
print("="*70)

# 1. Verificar health
test_api("GET", "/health", description="1. Health Check")

# 2. Verificar símbolo BTCUSDc
test_api("GET", "/symbol_info_tick/BTCUSDc", description="2. Tick BTCUSDc")

# 3. Verificar info do símbolo
test_api("GET", "/symbol_info/BTCUSDc", description="3. Info BTCUSDc")

# 4. Configurar bot para BTCUSDc
config_data = {
    "symbol": "BTCUSDc",
    "timeframe": "M1",
    "take_profit": 5000,
    "stop_loss": 10000,
    "confidence_threshold": 0.65,
    "auto_trading_enabled": True,
    "max_positions": 1
}
test_api("POST", "/mlp/config", config_data, description="4. Configurar Bot")

time.sleep(2)

# 5. Iniciar bot
test_api("POST", "/mlp/start", description="5. Iniciar Bot")

time.sleep(3)

# 6. Verificar status do bot
status = test_api("GET", "/mlp/status", description="6. Status do Bot")

time.sleep(2)

# 7. Tentar executar trade
execute_data = {
    "signal": "BUY",
    "confidence": 0.95,
    "symbol": "BTCUSDc"
}
result = test_api("POST", "/mlp/execute", execute_data, description="7. Executar Trade")

# Aguardar um pouco
time.sleep(3)

# 8. Verificar posições
test_api("GET", "/get_positions?symbol=BTCUSDc", description="8. Verificar Posições")

# 9. Parar bot
test_api("POST", "/mlp/stop", description="9. Parar Bot")

print("\n" + "="*70)
print("  FIM DO TESTE")
print("="*70)
