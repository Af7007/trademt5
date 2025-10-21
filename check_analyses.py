#!/usr/bin/env python3
import json
import urllib.request
import time

def check_analyses():
    print("Verificando análises após iniciar o bot...")

    try:
        with urllib.request.urlopen("http://localhost:5000/mlp/history?limit=5") as response:
            data = json.loads(response.read().decode())
            print(f"Total de análises: {data['count']}")

            if data['history']:
                print("Últimas análises encontradas:")
                for analysis in data['history'][:3]:
                    print(f"  - {analysis['signal']} {analysis['symbol']} (conf: {analysis['confidence']:.2f}) - {analysis['timestamp']}")
            else:
                print("  Nenhuma análise encontrada ainda")

    except Exception as e:
        print(f"Erro ao verificar análises: {e}")

if __name__ == "__main__":
    check_analyses()
