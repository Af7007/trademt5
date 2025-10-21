from services.mlp_storage import mlp_storage

print('=== MONITORANDO OPERACOES EM TEMPO REAL ===')
print('Aguardando sinais BUY/SELL com threshold 60%...')

# Verificar status atual
trades = mlp_storage.get_trades(symbol='XAUUSDc', days=1)
analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=5)

print(f'Trades atuais: {len(trades)}')
print(f'Ultimas analises: {len(analyses)}')

for i, analysis in enumerate(analyses):
    print(f'  {i+1}. {analysis["signal"]} ({analysis["confidence"]:.1%}) - {analysis["timestamp"]}')

print('')
print('Aguardando operacao...')
