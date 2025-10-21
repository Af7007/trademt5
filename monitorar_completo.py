from services.mlp_storage import mlp_storage

print('=== MONITORAMENTO CONTINUO - MINUTO A MINUTO ===')
print('')

tempo_espera = 5  # minutos
for minuto in range(tempo_espera):
    print(f'Minuto {minuto + 1}/{tempo_espera}:')

    # Verificar trades
    trades = mlp_storage.get_trades(symbol='XAUUSDc', days=1)
    if trades:
        print('  OPERACAO DETECTADA!')
        for trade in trades:
            print(f'    Ticket: {trade["ticket"]}')
            print(f'    Tipo: {trade["type"]}')
            print(f'    Volume: {trade["volume"]}')
            print(f'    Entrada: ${trade["entry_price"]:.2f}')
            print(f'    Lucro: ${trade["profit"]:.2f}')
            print(f'    Status: {"Aberto" if not trade["exit_time"] else "Fechado"}')
        break
    else:
        print('  Ainda sem operacoes')

    # Verificar ultima analise
    analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=1)
    if analyses:
        analysis = analyses[0]
        print(f'  Ultima analise: {analysis["signal"]} ({analysis["confidence"]:.1%})')

    if minuto < tempo_espera - 1:  # Não aguardar no último minuto
        import time
        print('  Aguardando 1 minuto...')
        time.sleep(60)

print('')
print('=== RESUMO FINAL ===')
total_analyses = len(mlp_storage.get_analyses(symbol='XAUUSDc', limit=1000))
total_trades = len(mlp_storage.get_trades(symbol='XAUUSDc', days=1))
print(f'Total de analises: {total_analyses}')
print(f'Total de trades: {total_trades}')
print(f'Status: {"Operacao executada!" if total_trades > 0 else "Aguardando oportunidade"}')
