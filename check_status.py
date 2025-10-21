#!/usr/bin/env python3
import json
import urllib.request

def check_status():
    try:
        with urllib.request.urlopen("http://localhost:5000/mlp/status") as response:
            data = json.loads(response.read().decode())
            print(f"Bot rodando: {data.get('is_running', False)}")
            print(f"MT5 conectado: {data.get('mt5_connected', False)}")
            print(f"Posições: {data.get('positions_count', 0)}")
            print(f"Uptime: {data.get('uptime', 'N/A')}")
    except Exception as e:
        print(f"Erro ao verificar status: {e}")

if __name__ == "__main__":
    check_status()
