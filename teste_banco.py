from services.mlp_storage import mlp_storage

print('Verificando logs no banco de dados...')
analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=5)
print(f'Análises encontradas: {len(analyses)}')

trades = mlp_storage.get_trades(symbol='XAUUSDc', days=1)
print(f'Trades encontrados: {len(trades)}')

print('Teste concluído!')
