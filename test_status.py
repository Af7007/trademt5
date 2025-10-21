import requests
import json

# Primeiro testar sem parâmetros
print("=== TESTE 1: Status básico ===")
try:
    response = requests.get('http://localhost:5000/mlp/status')
    print('Status Code:', response.status_code)
    print('Response Length:', len(response.text))
    print('Response:', response.text)

    if response.status_code == 200:
        data = response.json()
        print('Keys:', list(data.keys()))
except Exception as e:
    print('Error:', e)

print("\n=== TESTE 2: Status com parâmetros ===")
try:
    response = requests.get('http://localhost:5000/mlp/status?logs=5&analyses=3&trades=3')
    print('Status Code:', response.status_code)
    print('Response Length:', len(response.text))
    print('Response:', response.text[:1000])

    if response.status_code == 200:
        data = response.json()
        print('Keys:', list(data.keys()))
        print('Has logs:', 'logs' in data)
        print('Has recent_analyses:', 'recent_analyses' in data)
        print('Has recent_trades:', 'recent_trades' in data)
        print('Has config:', 'config' in data)
        print('Has system_status:', 'system_status' in data)
        print('Has webhook_connectivity:', 'webhook_connectivity' in data)
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()

print("\n=== TESTE 3: Verificar se há erro no servidor ===")
try:
    # Testar um endpoint que sabemos que funciona
    response = requests.get('http://localhost:5000/ping')
    print('Ping Status Code:', response.status_code)
    print('Ping Response:', response.text)
except Exception as e:
    print('Ping Error:', e)
