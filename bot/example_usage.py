#!/usr/bin/env python3
"""
Exemplo de uso do Bot MT5-MLP
"""
import os
import sys
import logging

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import get_config
    from mlp_model import MLPModel
except ImportError:
    # Fallback para execução direta
    from .config import get_config
    from .mlp_model import MLPModel


def exemplo_analise_basica():
    """Exemplo de análise básica sem conexão MT5"""
    print("=== Exemplo de Análise Básica ===")

    # Criar dados de exemplo
    import pandas as pd
    import numpy as np

    # Dados sintéticos de mercado
    dates = pd.date_range('2023-01-01', periods=100, freq='1min')
    np.random.seed(42)

    market_data = pd.DataFrame({
        'time': dates,
        'open': 100 + np.cumsum(np.random.randn(100) * 0.1),
        'high': 100 + np.cumsum(np.random.randn(100) * 0.1) + 0.5,
        'low': 100 + np.cumsum(np.random.randn(100) * 0.1) - 0.5,
        'close': 100 + np.cumsum(np.random.randn(100) * 0.1),
        'tick_volume': np.random.randint(10, 100, 100)
    })

    # Criar modelo
    model = MLPModel()

    # Gerar labels de treinamento
    labels = model.generate_training_labels(market_data)

    print(f"Dados de mercado: {len(market_data)} candles")
    print(f"Labels gerados: {len(labels)}")
    print(f"Distribuicao de sinais: BUY={np.sum(labels==0)}, SELL={np.sum(labels==1)}, HOLD={np.sum(labels==2)}")

    # Treinar modelo
    print("\nTreinando modelo...")
    results = model.train(market_data, labels)

    print("Resultado do treinamento:")
    print(f"  - Acuracia de treino: {results['train_accuracy']:.4f}")
    print(f"  - Acuracia de teste: {results['test_accuracy']:.4f}")
    print(f"  - Epocas treinadas: {results['epochs_trained']}")

    # Fazer predicao
    print("\nFazendo predicao...")
    signal, confidence = model.predict(market_data)

    print(f"Predicao: {signal} (Confianca: {confidence:.2f})")

    return model


def main():
    """Função principal"""
    print("Bot MT5-MLP - Exemplo de Uso")
    print("=" * 50)

    # Configurar logging básico
    logging.basicConfig(level=logging.INFO)

    # Executar exemplo
    model = exemplo_analise_basica()

    print("\n" + "=" * 50)
    print("Exemplo concluído!")
    print("\nPara usar o bot completo:")
    print("1. Configure o arquivo .env com suas credenciais MT5")
    print("2. Execute: python -m bot.main train --days 30")
    print("3. Execute: python -m bot.main bot --start-bot")
    print("4. Acesse a API em: http://localhost:5002")


if __name__ == "__main__":
    main()
