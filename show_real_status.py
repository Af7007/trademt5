#!/usr/bin/env python3
import json
import urllib.request

def show_real_status():
    try:
        with urllib.request.urlopen("http://localhost:5000/mlp/status") as response:
            data = json.loads(response.read().decode())

        print("=== STATUS REAL DO BOT MLP ===")
        print(f"Bot rodando: {data.get('is_running')}")
        print(f"MT5 conectado: {data.get('mt5_connected')}")
        print(f"Posições ativas: {data.get('positions_count')}")

        if data.get('positions'):
            for pos in data['positions']:
                print(f"  - {pos['ticket']}: {pos['type']} {pos['symbol']} @ volume {pos['volume']} (profit: ${pos['profit']:.2f})")

        account = data.get('account_info', {})
        print(f"Conta: ${account.get('balance', 0):.2f} {account.get('currency', '')}")
        print(f"Equity: ${account.get('equity', 0):.2f}")
        print(f"Margem livre: ${account.get('margin_free', 0):.2f}")

        last_pred = data.get('last_prediction', {})
        if last_pred:
            print(f"Última previsão: {last_pred.get('signal', 'Nenhuma')} ({last_pred.get('confidence', 0):.2f} confiança)")
        else:
            print("Última previsão: Nenhuma")

    except Exception as e:
        print(f"Erro ao obter status: {e}")

if __name__ == "__main__":
    show_real_status()
