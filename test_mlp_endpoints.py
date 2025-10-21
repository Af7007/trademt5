#!/usr/bin/env python3
import json
import urllib.request

def test_mlp_endpoints():
    base_url = "http://localhost:5000"

    # Testar health
    print("=== TESTANDO ENDPOINTS MLP ===")
    print("\n1. Testando /mlp/health...")
    try:
        with urllib.request.urlopen(f"{base_url}/mlp/health") as response:
            data = json.loads(response.read().decode())
            print(f"[OK] Status: {data.get('status')}")
            print(f"   Bot rodando: {data.get('bot_running')}")
            print(f"   MT5 conectado: {data.get('mt5_connected')}")
    except Exception as e:
        print(f"[ERRO] Erro: {e}")

    # Testar trades
    print("\n2. Testando /mlp/trades...")
    try:
        with urllib.request.urlopen(f"{base_url}/mlp/trades?days=7") as response:
            data = json.loads(response.read().decode())
            print(f"[OK] Total de trades: {data.get('count')}")
            for trade in data.get('trades', [])[:3]:
                print(f"   - {trade.get('ticket')}: {trade.get('type')} {trade.get('symbol')} @ {trade.get('entry_price')}")
    except Exception as e:
        print(f"[ERRO] Erro: {e}")

    # Testar history
    print("\n3. Testando /mlp/history...")
    try:
        with urllib.request.urlopen(f"{base_url}/mlp/history?limit=5") as response:
            data = json.loads(response.read().decode())
            print(f"[OK] Total de análises: {data.get('count')}")
            print(f"   Símbolo: {data.get('symbol')}")
    except Exception as e:
        print(f"[ERRO] Erro: {e}")

    # Testar analytics
    print("\n4. Testando /mlp/analytics...")
    try:
        with urllib.request.urlopen(f"{base_url}/mlp/analytics?days=7") as response:
            data = json.loads(response.read().decode())
            print(f"[OK] Total de estatísticas: {len(data.get('analytics', []))}")
            print(f"   Período: {data.get('period_days')} dias")
    except Exception as e:
        print(f"[ERRO] Erro: {e}")

    print("\n=== TESTES CONCLUÍDOS ===")

if __name__ == "__main__":
    test_mlp_endpoints()
