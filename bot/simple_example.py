#!/usr/bin/env python3
"""
Exemplo simples do Bot MT5-MLP
"""
import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import os


def criar_dados_exemplo():
    """Cria dados sintéticos de mercado"""
    dates = pd.date_range('2023-01-01', periods=100, freq='1min')
    np.random.seed(42)

    return pd.DataFrame({
        'time': dates,
        'open': 100 + np.cumsum(np.random.randn(100) * 0.1),
        'high': 100 + np.cumsum(np.random.randn(100) * 0.1) + 0.5,
        'low': 100 + np.cumsum(np.random.randn(100) * 0.1) - 0.5,
        'close': 100 + np.cumsum(np.random.randn(100) * 0.1),
        'tick_volume': np.random.randint(10, 100, 100)
    })


def calcular_indicadores(dados):
    """Calcula indicadores técnicos básicos"""
    df = dados.copy()

    # RSI simples
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Médias móveis
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()

    return df.fillna(0)


def gerar_labels(dados):
    """Gera labels de treinamento"""
    returns = dados['close'].pct_change()

    labels = []
    for ret in returns:
        if pd.isna(ret):
            labels.append(2)  # HOLD
        elif ret > 0.001:  # Alta
            labels.append(0)  # BUY
        elif ret < -0.001:  # Baixa
            labels.append(1)  # SELL
        else:
            labels.append(2)  # HOLD

    return np.array(labels)


def main():
    """Função principal"""
    print("Bot MT5-MLP - Exemplo Simples")
    print("=" * 40)

    # Criar dados
    print("1. Criando dados de exemplo...")
    dados_mercado = criar_dados_exemplo()
    print(f"   Dados criados: {len(dados_mercado)} candles")

    # Calcular indicadores
    print("2. Calculando indicadores técnicos...")
    dados_com_indicadores = calcular_indicadores(dados_mercado)
    print(f"   Indicadores calculados: {len(dados_com_indicadores.columns)} features")

    # Preparar dados para treinamento
    features = ['open', 'high', 'low', 'close', 'tick_volume', 'rsi', 'sma_20', 'sma_50']
    X = dados_com_indicadores[features].values

    # Normalizar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Gerar labels
    y = gerar_labels(dados_mercado)

    print("3. Preparando dados de treinamento...")
    print(f"   Features: {X_scaled.shape[1]}")
    print(f"   Samples: {X_scaled.shape[0]}")
    print(f"   Labels: BUY={np.sum(y==0)}, SELL={np.sum(y==1)}, HOLD={np.sum(y==2)}")

    # Criar e treinar modelo
    print("4. Treinando modelo MLP...")
    modelo = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        max_iter=100,
        random_state=42
    )

    modelo.fit(X_scaled, y)

    # Avaliar modelo
    acuracia_treino = modelo.score(X_scaled, y)
    print(f"   Acuracia de treino: {acuracia_treino:.4f}")

    # Fazer predição
    print("5. Fazendo predicao...")
    predicao = modelo.predict(X_scaled[-1:])
    probabilidade = modelo.predict_proba(X_scaled[-1:])

    sinais = {0: "BUY", 1: "SELL", 2: "HOLD"}
    sinal = sinais[predicao[0]]
    confianca = np.max(probabilidade)

    print(f"   Predicao: {sinal}")
    print(f"   Confianca: {confianca:.2f}")

    print("\n" + "=" * 40)
    print("Exemplo concluido com sucesso!")
    print("\nO modelo MLP foi treinado e fez uma predicao.")
    print("Para usar com MT5 real, configure suas credenciais")
    print("e execute: python -m bot.main train --days 30")


if __name__ == "__main__":
    main()
