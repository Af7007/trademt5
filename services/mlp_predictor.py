"""
MLP Predictor - Modelo de Machine Learning para Trading
Usa MLPClassifier do scikit-learn para prever sinais de trading
"""

import numpy as np
import pandas as pd
import logging
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class MLPPredictor:
    """Preditor MLP para sinais de trading"""
    
    def __init__(self, model_path='models/mlp_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Tentar carregar modelo existente
        self._load_model()
        
        # Se não existir, criar novo
        if not self.is_trained:
            self._create_model()
    
    def _create_model(self):
        """Cria um novo modelo MLP"""
        logger.info("Criando novo modelo MLP...")
        
        self.model = MLPClassifier(
            hidden_layer_sizes=(100, 50, 25),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            batch_size='auto',
            learning_rate='adaptive',
            learning_rate_init=0.001,
            max_iter=500,
            shuffle=True,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10
        )
        
        logger.info("Modelo MLP criado (não treinado)")
    
    def _load_model(self):
        """Carrega modelo salvo"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.is_trained = True
                logger.info(f"Modelo MLP carregado de {self.model_path}")
            except Exception as e:
                logger.error(f"Erro ao carregar modelo: {e}")
                self.is_trained = False
    
    def _save_model(self):
        """Salva modelo treinado"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'trained_at': datetime.now().isoformat()
                }, f)
            
            logger.info(f"Modelo salvo em {self.model_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar modelo: {e}")
    
    def _prepare_features(self, df):
        """Prepara features do DataFrame"""
        features = []
        
        # RSI
        close = df['close'].values
        deltas = np.diff(close)
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0
        rsi = 100 - (100 / (1 + (avg_gain / avg_loss))) if avg_loss > 0 else 50
        features.append(rsi)
        
        # SMA
        sma_20 = np.mean(close[-20:]) if len(close) >= 20 else close[-1]
        sma_50 = np.mean(close[-50:]) if len(close) >= 50 else close[-1]
        features.append(sma_20)
        features.append(sma_50)
        
        # Preço atual
        current_price = close[-1]
        features.append(current_price)
        
        # Distância das SMAs
        dist_sma20 = (current_price - sma_20) / sma_20 * 100
        dist_sma50 = (current_price - sma_50) / sma_50 * 100
        features.append(dist_sma20)
        features.append(dist_sma50)
        
        # Tendência
        trend = 1 if sma_20 > sma_50 else -1
        features.append(trend)
        
        # Volatilidade (desvio padrão dos últimos 20 períodos)
        volatility = np.std(close[-20:]) if len(close) >= 20 else 0
        features.append(volatility)
        
        # Momentum (diferença percentual dos últimos 5 períodos)
        momentum = (close[-1] - close[-5]) / close[-5] * 100 if len(close) >= 5 else 0
        features.append(momentum)
        
        return np.array(features).reshape(1, -1)
    
    def train(self, training_data):
        """
        Treina o modelo com dados históricos
        
        Args:
            training_data: Lista de dicts com 'features' e 'label'
                          label: 0=SELL, 1=HOLD, 2=BUY
        """
        if len(training_data) < 50:
            logger.warning("Dados insuficientes para treinar (mínimo 50 amostras)")
            return False
        
        X = np.array([item['features'] for item in training_data])
        y = np.array([item['label'] for item in training_data])
        
        # Normalizar features
        X_scaled = self.scaler.fit_transform(X)
        
        # Treinar modelo
        logger.info(f"Treinando modelo com {len(training_data)} amostras...")
        self.model.fit(X_scaled, y)
        
        # Calcular acurácia
        score = self.model.score(X_scaled, y)
        logger.info(f"Modelo treinado! Acurácia: {score*100:.2f}%")
        
        self.is_trained = True
        self._save_model()
        
        return True
    
    def predict(self, df):
        """
        Faz predição baseada no DataFrame
        
        Args:
            df: DataFrame com colunas ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
            tuple: (signal, confidence)
                   signal: 'BUY', 'SELL', 'HOLD'
                   confidence: float entre 0 e 1
        """
        if not self.is_trained:
            logger.warning("Modelo não treinado, usando lógica baseada em indicadores")
            return self._fallback_prediction(df)
        
        try:
            # Preparar features
            features = self._prepare_features(df)
            
            # Normalizar
            features_scaled = self.scaler.transform(features)
            
            # Predição
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Converter para sinal
            signal_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
            signal = signal_map[prediction]
            confidence = probabilities[prediction]
            
            logger.info(f"MLP Predição: {signal} ({confidence*100:.1f}%)")
            logger.debug(f"Probabilidades: SELL={probabilities[0]*100:.1f}%, HOLD={probabilities[1]*100:.1f}%, BUY={probabilities[2]*100:.1f}%")
            
            return signal, confidence
            
        except Exception as e:
            logger.error(f"Erro na predição MLP: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._fallback_prediction(df)
    
    def _fallback_prediction(self, df):
        """Predição de fallback usando indicadores técnicos"""
        logger.info("Usando predição de fallback (indicadores)")
        
        close = df['close'].values
        
        # RSI
        deltas = np.diff(close)
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0
        rsi = 100 - (100 / (1 + (avg_gain / avg_loss))) if avg_loss > 0 else 50
        
        # SMA
        sma_20 = np.mean(close[-20:]) if len(close) >= 20 else close[-1]
        sma_50 = np.mean(close[-50:]) if len(close) >= 50 else close[-1]
        
        # Lógica simples
        if rsi < 30:
            return 'BUY', 0.75
        elif rsi > 70:
            return 'SELL', 0.75
        elif rsi < 40 and close[-1] < sma_20:
            return 'BUY', 0.65
        elif rsi > 60 and close[-1] > sma_20:
            return 'SELL', 0.65
        elif close[-1] > sma_20 > sma_50:
            return 'BUY', 0.55
        elif close[-1] < sma_20 < sma_50:
            return 'SELL', 0.55
        else:
            return 'HOLD', 0.50
    
    def auto_train_from_mt5(self, symbol='BTCUSDc', timeframe='M1', num_samples=500):
        """
        Treina o modelo automaticamente usando dados históricos do MT5
        
        Args:
            symbol: Símbolo para coletar dados
            timeframe: Timeframe (M1, M5, etc)
            num_samples: Número de amostras para treinar
        
        Returns:
            bool: True se treinou com sucesso
        """
        try:
            import MetaTrader5 as mt5
            
            logger.info(f"Iniciando treinamento automático do MLP...")
            logger.info(f"Símbolo: {symbol}, Timeframe: {timeframe}, Amostras: {num_samples}")
            
            if not mt5.initialize():
                logger.error("Falha ao conectar MT5")
                return False
            
            # Mapear timeframe
            timeframe_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }
            
            tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_M1)
            
            # Coletar dados históricos (pegar mais para ter contexto)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, num_samples + 100)
            
            if rates is None or len(rates) < 100:
                logger.error("Dados insuficientes do MT5")
                return False
            
            df_full = pd.DataFrame(rates)
            df_full['time'] = pd.to_datetime(df_full['time'], unit='s')
            
            logger.info(f"Coletados {len(df_full)} candles históricos")
            
            # Calcular threshold adaptativo baseado na volatilidade do símbolo
            all_returns = np.diff(df_full['close'].values) / df_full['close'].values[:-1] * 100
            volatility = np.std(all_returns)
            threshold = max(0.05, volatility * 0.5)  # Mínimo 0.05%, ou metade da volatilidade
            
            logger.info(f"Volatilidade do {symbol}: {volatility:.4f}%")
            logger.info(f"Threshold para classificação: {threshold:.4f}%")
            
            # Gerar dados de treinamento
            training_data = []
            
            for i in range(100, len(df_full) - 10):  # Deixar espaço para lookahead
                # Pegar janela de dados até o ponto i
                df_window = df_full.iloc[:i+1].copy()
                
                # Extrair features
                features = self._prepare_features(df_window).flatten()
                
                # Determinar label olhando para frente (10 períodos)
                future_prices = df_full.iloc[i+1:i+11]['close'].values
                current_price = df_full.iloc[i]['close']
                
                # Calcular mudança percentual
                max_gain = (np.max(future_prices) - current_price) / current_price * 100
                max_loss = (current_price - np.min(future_prices)) / current_price * 100
                
                # Classificar baseado no movimento futuro (usando threshold adaptativo)
                if max_gain > threshold and max_gain > max_loss * 1.2:  # Subiu significativamente
                    label = 2  # BUY
                elif max_loss > threshold and max_loss > max_gain * 1.2:  # Caiu significativamente
                    label = 0  # SELL
                else:
                    label = 1  # HOLD
                
                training_data.append({
                    'features': features,
                    'label': label
                })
            
            logger.info(f"Geradas {len(training_data)} amostras de treinamento")
            
            # Contar distribuição
            buy_count = sum(1 for d in training_data if d['label'] == 2)
            sell_count = sum(1 for d in training_data if d['label'] == 0)
            hold_count = sum(1 for d in training_data if d['label'] == 1)
            
            logger.info(f"Distribuição original: BUY={buy_count}, SELL={sell_count}, HOLD={hold_count}")
            
            # Balancear classes para evitar viés
            buy_samples = [d for d in training_data if d['label'] == 2]
            sell_samples = [d for d in training_data if d['label'] == 0]
            hold_samples = [d for d in training_data if d['label'] == 1]
            
            # Pegar o mínimo entre BUY e SELL (ignorar HOLD para balancear)
            min_count = min(len(buy_samples), len(sell_samples))
            
            if min_count > 0:
                # Shuffle para randomizar
                np.random.shuffle(buy_samples)
                np.random.shuffle(sell_samples)
                np.random.shuffle(hold_samples)
                
                # Balancear BUY e SELL - pegar exatamente min_count de cada
                buy_balanced = buy_samples[:min_count]
                sell_balanced = sell_samples[:min_count]
                
                # Reduzir HOLD para não dominar (50% do min_count)
                hold_target = max(10, min_count // 2)
                hold_balanced = hold_samples[:min(hold_target, len(hold_samples))]
                
                training_data_balanced = buy_balanced + sell_balanced + hold_balanced
                
                # Shuffle final para misturar tudo
                np.random.shuffle(training_data_balanced)
                
                logger.info(f"Distribuição balanceada: BUY={len(buy_balanced)}, SELL={len(sell_balanced)}, HOLD={len(hold_balanced)}")
                training_data = training_data_balanced
            else:
                logger.warning("Não há amostras suficientes de BUY ou SELL para balancear!")
            
            # Treinar modelo
            success = self.train(training_data)
            
            if success:
                logger.info("✓ Modelo MLP treinado com sucesso!")
            else:
                logger.error("✗ Falha ao treinar modelo MLP")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro no treinamento automático: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False


# Instância global
mlp_predictor = MLPPredictor()
