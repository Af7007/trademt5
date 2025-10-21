from services.mlp_storage import mlp_storage
import time

print('=== MONITORANDO ANALISES EM TEMPO REAL ===')
print('Aguardando sinais BUY/SELL...')

for i in range(10):  # Verificar 10 vezes
    analyses = mlp_storage.get_analyses(symbol='XAUUSDc', limit=1)
    if analyses:
        analysis = analyses[0]
        print(f'Analise {i+1}: {analysis["signal"]} (confianca: {analysis["confidence"]:.2f})')

        if analysis['signal'] in ['BUY', 'SELL']:
            print(f'*** SINAL DETECTADO: {analysis["signal"]} ***')
            break

    time.sleep(10)

print('Monitoramento concluido')
