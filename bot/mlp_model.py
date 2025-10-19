"""
Modelo MLP para análise de mercado e predição de sinais de trading
"""
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os
import logging
from typing import Tuple, Dict, Any
import joblib

from .config import get_config


class MarketDataPreprocessor:
    """Pré-processamento de dados de mercado para o modelo MLP"""

    def __init__(self):
        self.config = get_config()
        self.scaler = StandardScaler()
        self.feature_scaler = StandardScaler()

    def prepare_features(self, market_data: pd.DataFrame) -> np.ndarray:
        """Prepara features para o modelo"""
        # Calcula indicadores técnicos
        features = self._calculate_technical_indicators(market_data)

        # Seleciona features configuradas
        selected_features = []
        for feature in self.config.mlp.features:
            if feature in features.columns:
                selected_features.append(feature)

        if not selected_features:
            raise ValueError("Nenhuma feature válida encontrada nos dados")

        feature_data = features[selected_features].values

        # Normaliza dados
        if len(feature_data) > 0:
            feature_data = self.scaler.fit_transform(feature_data)

        return feature_data

    def _calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos"""
        df = data.copy()

        # RSI
        df['rsi'] = self._calculate_rsi(df['close'])

        # MACD
        df['macd'], df['macd_signal'], df['macd_histogram'] = self._calculate_macd(df['close'])

        # Médias móveis
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()

        # Bandas de Bollinger
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

        # Williams %R
        df['williams_r'] = self._calculate_williams_r(df)

        # Retorna apenas colunas necessárias
        return df.fillna(0)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calcula RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcula MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        return macd, macd_signal, macd_histogram

    def _calculate_williams_r(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcula Williams %R"""
        highest_high = data['high'].rolling(window=period).max()
        lowest_low = data['low'].rolling(window=period).min()
        return -100 * (highest_high - data['close']) / (highest_high - lowest_low)


class MLPModel:
    """Modelo MLP para predição de sinais de trading usando scikit-learn"""

    def __init__(self, model_path: str = None):
        self.config = get_config()
        self.model = None
        self.preprocessor = MarketDataPreprocessor()
        self.model_path = model_path or self.config.model_save_path + "mlp_model.pkl"

        # Configurar logging
        self.logger = logging.getLogger(__name__)

    def build_model(self) -> MLPClassifier:
        """Constrói modelo MLP usando scikit-learn"""
        # Criar arquitetura baseada na configuração
        hidden_layers = self.config.mlp.hidden_layers

        # scikit-learn usa tupla para camadas ocultas
        hidden_layer_sizes = tuple(hidden_layers)

        model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation='relu',
            solver='adam',
            learning_rate_init=self.config.mlp.learning_rate,
            max_iter=self.config.mlp.epochs,
            batch_size=self.config.mlp.batch_size,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.2,
            n_iter_no_change=10
        )

        return model

    def train(self, market_data: pd.DataFrame, labels: np.ndarray) -> Dict[str, Any]:
        """Treina o modelo MLP"""
        try:
            # Preparar dados
            features = self.preprocessor.prepare_features(market_data)

            if len(features) == 0:
                raise ValueError("Dados de features vazios")

            # Dividir dados
            X_train, X_test, y_train, y_test = train_test_split(
                features, labels, test_size=0.2, random_state=42
            )

            # Construir modelo se não existir
            if self.model is None:
                self.model = self.build_model()

            # Treinar modelo
            self.model.fit(X_train, y_train)

            # Avaliar modelo
            train_accuracy = self.model.score(X_train, y_train)
            test_accuracy = self.model.score(X_test, y_test)

            # Fazer predições no conjunto de teste
            y_pred = self.model.predict(X_test)
            test_accuracy_manual = accuracy_score(y_test, y_pred)

            # Salvar scaler
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            joblib.dump(self.preprocessor.scaler, self.model_path.replace('.pkl', '_scaler.pkl'))

            # Resultados
            results = {
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'test_accuracy_manual': test_accuracy_manual,
                'epochs_trained': self.model.n_iter_,
                'best_loss': self.model.best_loss_ if hasattr(self.model, 'best_loss_') else None
            }

            self.logger.info(f"Modelo treinado com sucesso. Test Accuracy: {test_accuracy:.4f}")
            return results

        except Exception as e:
            self.logger.error(f"Erro ao treinar modelo: {str(e)}")
            raise

    def predict(self, market_data: pd.DataFrame) -> Tuple[str, float]:
        """Faz predição usando o modelo treinado"""
        try:
            if self.model is None:
                self.load_model()

            # Preparar dados
            features = self.preprocessor.prepare_features(market_data)

            if len(features) == 0:
                return "HOLD", 0.5

            # Fazer predição
            predictions = self.model.predict_proba(features)
            predicted_class = self.model.predict(features)[-1]  # Última predição
            confidence = np.max(predictions[-1])  # Última probabilidade

            # Converter para sinal de trading
            signal_map = {0: "BUY", 1: "SELL", 2: "HOLD"}
            signal = signal_map[predicted_class]

            return signal, float(confidence)

        except Exception as e:
            self.logger.error(f"Erro na predição: {str(e)}")
            return "HOLD", 0.5

    def save_model(self):
        """Salva o modelo treinado"""
        try:
            if self.model:
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                joblib.dump(self.model, self.model_path)
                self.logger.info(f"Modelo salvo em: {self.model_path}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar modelo: {str(e)}")

    def load_model(self):
        """Carrega modelo treinado"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)

                # Carregar scaler
                scaler_path = self.model_path.replace('.pkl', '_scaler.pkl')
                if os.path.exists(scaler_path):
                    self.preprocessor.scaler = joblib.load(scaler_path)

                self.logger.info(f"Modelo carregado de: {self.model_path}")
            else:
                self.logger.warning(f"Modelo não encontrado em: {self.model_path}")
                self.model = self.build_model()
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo: {str(e)}")
            self.model = self.build_model()

    def generate_training_labels(self, market_data: pd.DataFrame) -> np.ndarray:
        """Gera labels de treinamento baseados nos dados históricos"""
        # Estratégia simples: baseado no movimento do preço
        returns = market_data['close'].pct_change()

        # Labels: 0=BUY, 1=SELL, 2=HOLD
        labels = []
        for ret in returns:
            if pd.isna(ret):
                labels.append(2)  # HOLD para dados iniciais
            elif ret > 0.001:  # Retorno positivo > 0.1%
                labels.append(0)  # BUY
            elif ret < -0.001:  # Retorno negativo < -0.1%
                labels.append(1)  # SELL
            else:
                labels.append(2)  # HOLD

        return np.array(labels)
