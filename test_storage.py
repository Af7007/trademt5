#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.mlp_storage import mlp_storage
from datetime import datetime

def test_storage():
    print("Testando armazenamento MLP...")

    # Dados de teste
    test_analysis = {
        'symbol': 'BTCUSDc',
        'signal': 'SELL',
        'confidence': 0.9999999954691579,
        'timestamp': datetime.now().isoformat(),
        'indicators': {
            'rsi': 45.5,
            'macd_signal': -0.001,
            'bb_upper': 112000.0,
            'bb_lower': 109000.0,
            'sma_20': 110500.0,
            'sma_50': 110800.0,
        },
        'market_data': {
            'open': 110900.0,
            'high': 111000.0,
            'low': 110800.0,
            'close': 110967.61,
            'volume': 100.0,
        }
    }

    try:
        # Tentar adicionar análise
        analysis_id = mlp_storage.add_analysis(test_analysis)
        print(f"Análise adicionada com sucesso - ID: {analysis_id}")

        # Verificar se foi salva
        analyses = mlp_storage.get_analyses(limit=5)
        print(f"Total de análises após adicionar: {len(analyses)}")

        if analyses:
            print("Última análise salva:")
            print(f"  - Símbolo: {analyses[0]['symbol']}")
            print(f"  - Sinal: {analyses[0]['signal']}")
            print(f"  - Confiança: {analyses[0]['confidence']}")
            print(f"  - Timestamp: {analyses[0]['timestamp']}")

        return True

    except Exception as e:
        print(f"Erro ao testar armazenamento: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_storage()
