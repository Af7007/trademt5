from services.mlp_storage import mlp_storage

print('=== AGUARDANDO OPERACAO - MODO AGRESSIVO ===')
print('Threshold: 60% | Símbolo: XAUUSDc | Lucro: $0.50')
print('')

# Verificar se há trades
trades = mlp_storage.get_trades(symbol='XAUUSDc', days=1)
if trades:
    print('OPERACOES ENCONTRADAS!')
    for trade in trades:
        print(f'  Ticket: {trade["ticket"]}')
        print(f'  Tipo: {trade["type"]}')
        print(f'  Volume: {trade["volume"]}')
        print(f'  Entrada: ${trade["entry_price"]:.2f}')
        print(f'  Lucro: ${trade["profit"]:.2f}')
        print(f'  Status: {"Aberto" if not trade["exit_time"] else "Fechado"}')
else:
    print('Ainda sem operacoes - continuando monitoramento...')
    print('')

# Mostrar ultimas analises
analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=3)
print('Ultimas analises:')
for analysis in analyses:
    print(f'  {analysis["signal"]} ({analysis["confidence"]:.1%}) - {analysis["timestamp"]}')

print('')
print('Bot rodando... Aguardando oportunidade de operacao...')
