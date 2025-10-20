#!/usr/bin/env python3
"""
Script para treinar modelo MLP usando dados históricos do MT5
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constantes
SYMBOL = "BTCUSDc"
TIMEFRAME = mt5.TIMEFRAME_M1
DAYS_HISTORY = 30  # Dias de dados históricos
MODEL_PATH = "bot/models/mlp_model.pkl"

def conectar_mt5():
    """Conecta no MT5"""
    if not mt5.initialize():
        raise Exception("Falha ao inicializar MT5")

    if not mt5.symbol_select(SYMBOL, True):
        raise Exception(f"Símbolo {SYMBOL} não disponível")

    logger.info(f"MT5 conectado - {SYMBOL}")
    return True

def obter_dados_historicos():
    """Obtém dados históricos do MT5"""
    logger.info(f"Obtendo {DAYS_HISTORY} dias de dados históricos...")

    # Definir período
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_HISTORY)

    # Converter para datetime do MT5
    utc_from = start_date
    utc_to = end_date

    # Obter dados
    rates = mt5.copy_rates_range(SYMBOL, TIMEFRAME, utc_from, utc_to)

    if rates is None or len(rates) == 0:
        raise Exception("Falha ao obter dados históricos")

    # Converter para DataFrame
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    logger.info(f"Obtidos {len(df)} candles históricos")
    return df

def calcular_indicadores(df):
    """Calcula indicadores técnicos"""
    df = df.copy()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Médias móveis
    df['sma_10'] = df['close'].rolling(window=10).mean()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    df['bb_std'] = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

    # Retornos para labels
    df['returns'] = df['close'].pct_change()

    return df.fillna(0)

def gerar_labels(df):
    """Gera labels de treinamento baseados nos retornos futuros"""
    labels = []

    for i in range(len(df)):
        if i == len(df) - 1:
            # Último elemento - não temos retorno futuro
            labels.append(2)  # HOLD
        else:
            # Baseado no próximo retorno
            future_return = df['returns'].iloc[i + 1]

            if pd.isna(future_return):
                labels.append(2)  # HOLD
            elif future_return > 0.0005:  # Retorno positivo mínimo
                labels.append(0)  # BUY
            elif future_return < -0.0005:  # Retorno negativo mínimo
                labels.append(1)  # SELL
            else:
                labels.append(2)  # HOLD (consolidação)

    return np.array(labels)

def treinar_modelo():
    """Treina o modelo MLP"""
    try:
        # Conectar MT5
        conectar_mt5()

        # Obter dados
        df = obter_dados_historicos()

        # Calcular indicadores
        df = calcular_indicadores(df)

        # Definir features
        features = ['open', 'high', 'low', 'close', 'tick_volume', 'rsi', 'sma_10', 'sma_20', 'sma_50']

        # Dados de treinamento (usar dados históricos)
        X_train = df[features].values[:-500]  # Últimos 500 para teste
        y_train = gerar_labels(df)[:-500]

        # Dados de teste
        X_test = df[features].values[-500:]
        y_test = gerar_labels(df)[-500:]

        # Verificar se temos dados suficientes
        if len(X_train) < 1000:
            raise Exception("Dados insuficientes para treinamento")

        logger.info(f"Treinamento: {len(X_train)} samples, Teste: {len(X_test)} samples")
        logger.info(f"Distribuição labels - BUY: {np.sum(y_train==0)}, SELL: {np.sum(y_train==1)}, HOLD: {np.sum(y_train==2)}")

        # Normalizar dados
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Criar modelo MLP
        model = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation='relu',
            solver='adam',
            learning_rate_init=0.001,
            max_iter=100,
            batch_size=32,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.2,
            n_iter_no_change=10
        )

        # Treinar modelo
        logger.info("Treinando modelo MLP...")
        model.fit(X_train_scaled, y_train)

        # Avaliar modelo
        train_accuracy = model.score(X_train_scaled, y_train)
        test_accuracy = model.score(X_test_scaled, y_test)

        logger.info(f"Acuracia Treino: {train_accuracy:.4f}")
        logger.info(f"Acuracia Teste: {test_accuracy:.4f}")

        # Salvar modelo
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, MODEL_PATH.replace('.pkl', '_scaler.pkl'))

        logger.info(f"Modelo salvo em {MODEL_PATH}")

        # Resultado
        result = {
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'samples_train': len(X_train),
            'samples_test': len(X_test)
        }

        return result

    finally:
        # Finalizar MT5
        mt5.shutdown()

def main():
    """Função principal"""
    try:
        print("=" * 60)
        print("TREINAMENTO DE MODELO MLP DE TRADING")
        print("=" * 60)
        print(f"Símbolo: {SYMBOL}")
        print(f"Timeframe: M1")
        print(f"Dados Históricos: {DAYS_HISTORY} dias")
        print("=" * 60)

        results = treinar_modelo()

        print("\n" + "=" * 60)
        print("TREINAMENTO CONCLUÍDO COM SUCESSO!")
        print(".1f")
        print(".1f")
        print("=" * 60)

        print(f"Modelo salvo: {MODEL_PATH}")
        print("Agora você pode executar: py -3.8 bot_mt5_direct.py")

    except Exception as e:
        logger.error(f"Falha no treinamento: {e}")
        return False

    return True

if __name__ == "__main__":
    main()
