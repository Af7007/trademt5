from services.mlp_storage import mlp_storage

print('=== STATUS ATUAL DO BANCO ===')
analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=5)
print(f'Analises: {len(analyses)}')
for a in analyses:
    print(f'  {a["id"]}: {a["signal"]} ({a["confidence"]:.2f}) - {a["timestamp"]}')

trades = mlp_storage.get_trades(symbol='XAUUSDc', days=1)
print(f'Trades: {len(trades)}')
for t in trades:
    print(f'  {t["ticket"]}: {t["type"]} - Lucro: ${t["profit"]:.2f}')
