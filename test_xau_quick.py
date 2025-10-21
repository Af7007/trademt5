import requests
import json

# Testar execução direta
print("Testando execução de trade XAU...")

response = requests.post(
    'http://localhost:5000/mlp/execute',
    json={
        'signal': 'BUY',
        'confidence': 0.95,
        'symbol': 'XAUUSDc'
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
