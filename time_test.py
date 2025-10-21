#!/usr/bin/env python3
"""
Teste de horários MT5 vs Local
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5
from core.mt5_connection import MT5Connection

def test_times():
    """Testa horários do sistema vs MT5"""
    print("⏰ TESTANDO HORÁRIOS MT5 VS LOCAL")
    print("=" * 50)

    # Conectar ao MT5
    mt5_conn = MT5Connection()
    try:
        mt5_conn.initialize()

        # Horário local
        local_time = datetime.now()
        print("🕐 HORÁRIO LOCAL (Python datetime.now()): {}".format(local_time))

        # Hora do terminal MT5
        terminal = mt5.terminal_info()
        if terminal:
            if hasattr(terminal, 'datetime'):
                terminal_time = getattr(terminal, 'datetime')
                if terminal_time:
                    print("🖥️  HORÁRIO TERMINAL MT5: {}".format(datetime.fromtimestamp(terminal_time)))
                else:
                    print("🖥️  HORÁRIO TERMINAL MT5: Não disponível")
            else:
                print("🖥️  HORÁRIO TERMINAL MT5: Atributo datetime não encontrado")
        else:
            print("❌ Não conseguiu obter horário do terminal")

        # Hora do servidor via account
        account = mt5.account_info()
        if account:
            print("🗄️  SERVIDOR MT5: {}".format(account.server))

            # Obter horário do servidor via dados de mercado
            print("📊 Testando dados de mercado...")
            rates = mt5.copy_rates_from_pos('BTCUSDc', mt5.TIMEFRAME_M5, 0, 1)
            if rates is not None and len(rates) > 0:
                last_rate = rates[-1]
                timestamp = int(last_rate[0])  # Converter para int se necessário
                server_time = pd.to_datetime(timestamp, unit='s')
                print("📊 HORÁRIO ÚLTIMO CANDLE (servidor GMT): {}".format(server_time))

                # Diferença
                local_diff = local_time - server_time.to_pydatetime().replace(tzinfo=None)
                print("⚡ DIFERENÇA: Local - Server = {:.2f} segundos".format(local_diff.total_seconds()))

                # GMT convertido
                gmt_time = local_time - timedelta(hours=3)  # UTC-3
                gmt_diff = gmt_time - server_time.to_pydatetime().replace(tzinfo=None)
                print("🌍 GMT Convertido (UTC-3): {} | Dif: {:.2f}s".format(gmt_time, gmt_diff.total_seconds()))

            else:
                print("❌ Não conseguiu obter dados de mercado")
        else:
            print("❌ Não conseguiu obter dados da conta MT5")

        mt5.shutdown()

    except Exception as e:
        print("❌ ERRO GERAL: {}".format(e))
        import traceback
        traceback.print_exc()

    print("=" * 50)
