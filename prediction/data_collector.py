"""
Data Collector - Coleta de dados do MT5
Responsável por coletar informações de mercado, histórico e estatísticas
"""

import logging
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from core.mt5_connection import mt5_connection

logger = logging.getLogger(__name__)


class DataCollector:
    """Coleta dados do MT5 para análise e predição"""
    
    def __init__(self):
        self.mt5_connection = mt5_connection
        self.cache = {}
        self.cache_ttl = 60  # segundos
    
    def ensure_connection(self) -> bool:
        """Garante que a conexão com MT5 está ativa"""
        try:
            self.mt5_connection.ensure_connection()
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar MT5: {e}")
            return False
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """
        Obtém informações detalhadas sobre um símbolo
        
        Args:
            symbol: Nome do símbolo (ex: XAUUSDc)
            
        Returns:
            Dicionário com informações do símbolo
        """
        if not self.ensure_connection():
            return None
        
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Símbolo {symbol} não encontrado")
                return None
            
            return {
                'name': symbol_info.name,
                'description': symbol_info.description,
                'point': symbol_info.point,
                'digits': symbol_info.digits,
                'spread': symbol_info.spread,
                'spread_float': symbol_info.spread_float,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step,
                'trade_tick_value': symbol_info.trade_tick_value,
                'trade_tick_size': symbol_info.trade_tick_size,
                'trade_contract_size': symbol_info.trade_contract_size,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'last': symbol_info.last,
                'session_deals': symbol_info.session_deals,
                'session_buy_orders': symbol_info.session_buy_orders,
                'session_sell_orders': symbol_info.session_sell_orders,
                'volume': symbol_info.volume,
                'volumehigh': symbol_info.volumehigh,
                'volumelow': symbol_info.volumelow
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações do símbolo {symbol}: {e}")
            return None
    
    def get_historical_data(
        self,
        symbol: str,
        timeframe: int,
        bars: int = 1000
    ) -> Optional[pd.DataFrame]:
        """
        Obtém dados históricos de preços
        
        Args:
            symbol: Nome do símbolo
            timeframe: Timeframe MT5 (mt5.TIMEFRAME_M1, etc)
            bars: Número de barras a coletar
            
        Returns:
            DataFrame com dados históricos
        """
        if not self.ensure_connection():
            return None
        
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            if rates is None or len(rates) == 0:
                logger.error(f"Não foi possível obter dados históricos para {symbol}")
                return None
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Erro ao obter dados históricos: {e}")
            return None
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula indicadores técnicos
        
        Args:
            df: DataFrame com dados de preços
            
        Returns:
            DataFrame com indicadores adicionados
        """
        try:
            # SMA (Simple Moving Average)
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            
            # EMA (Exponential Moving Average)
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd'] - df['signal']
            
            # RSI (Relative Strength Index)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            
            # ATR (Average True Range)
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()
            
            # Volume analysis
            df['volume_sma'] = df['tick_volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['tick_volume'] / df['volume_sma']
            
            # Price momentum
            df['momentum'] = df['close'].pct_change(periods=10)
            df['rate_of_change'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
            
            # Volatilidade
            df['volatility'] = df['close'].rolling(window=20).std()
            
            return df
        except Exception as e:
            logger.error(f"Erro ao calcular indicadores: {e}")
            return df
    
    def get_market_depth(self, symbol: str) -> Optional[Dict]:
        """
        Obtém profundidade de mercado (order book)
        
        Args:
            symbol: Nome do símbolo
            
        Returns:
            Dicionário com informações de mercado
        """
        if not self.ensure_connection():
            return None
        
        try:
            # Obter tick mais recente
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            return {
                'time': datetime.fromtimestamp(tick.time),
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volume': tick.volume,
                'spread': tick.ask - tick.bid,
                'spread_points': (tick.ask - tick.bid) / mt5.symbol_info(symbol).point
            }
        except Exception as e:
            logger.error(f"Erro ao obter profundidade de mercado: {e}")
            return None
    
    def get_historical_trades(
        self,
        symbol: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Obtém histórico de trades executados
        
        Args:
            symbol: Nome do símbolo (opcional)
            days: Número de dias para buscar
            
        Returns:
            Lista de trades
        """
        if not self.ensure_connection():
            return []
        
        try:
            from_date = datetime.now() - timedelta(days=days)
            to_date = datetime.now()
            
            deals = mt5.history_deals_get(from_date, to_date)
            if deals is None:
                return []
            
            trades = []
            for deal in deals:
                if symbol and deal.symbol != symbol:
                    continue
                
                trades.append({
                    'ticket': deal.ticket,
                    'order': deal.order,
                    'time': datetime.fromtimestamp(deal.time),
                    'type': 'BUY' if deal.type == mt5.DEAL_TYPE_BUY else 'SELL',
                    'entry': 'IN' if deal.entry == mt5.DEAL_ENTRY_IN else 'OUT',
                    'volume': deal.volume,
                    'price': deal.price,
                    'profit': deal.profit,
                    'symbol': deal.symbol,
                    'commission': deal.commission,
                    'swap': deal.swap,
                    'comment': deal.comment
                })
            
            return trades
        except Exception as e:
            logger.error(f"Erro ao obter histórico de trades: {e}")
            return []
    
    def analyze_trading_patterns(
        self,
        symbol: str,
        timeframe: int,
        days: int = 30
    ) -> Dict:
        """
        Analisa padrões de trading históricos
        
        Args:
            symbol: Nome do símbolo
            timeframe: Timeframe MT5
            days: Número de dias para análise
            
        Returns:
            Dicionário com padrões identificados
        """
        try:
            # Obter dados históricos
            bars = days * 24 * 60  # Aproximação para M1
            if timeframe == mt5.TIMEFRAME_M5:
                bars = bars // 5
            elif timeframe == mt5.TIMEFRAME_M15:
                bars = bars // 15
            elif timeframe == mt5.TIMEFRAME_H1:
                bars = bars // 60
            elif timeframe == mt5.TIMEFRAME_H4:
                bars = bars // 240
            elif timeframe == mt5.TIMEFRAME_D1:
                bars = days
            
            df = self.get_historical_data(symbol, timeframe, bars)
            if df is None:
                return {}
            
            # Calcular indicadores
            df = self.calculate_indicators(df)
            
            # Análise de padrões
            patterns = {
                'trend': self._identify_trend(df),
                'support_resistance': self._find_support_resistance(df),
                'volatility': self._analyze_volatility(df),
                'volume_profile': self._analyze_volume(df),
                'best_trading_hours': self._find_best_hours(df),
                'win_rate_by_direction': self._calculate_win_rates(symbol, days)
            }
            
            return patterns
        except Exception as e:
            logger.error(f"Erro ao analisar padrões de trading: {e}")
            return {}
    
    def _identify_trend(self, df: pd.DataFrame) -> Dict:
        """Identifica tendência do mercado"""
        try:
            current_price = df['close'].iloc[-1]
            sma_20 = df['sma_20'].iloc[-1]
            sma_50 = df['sma_50'].iloc[-1]
            sma_200 = df['sma_200'].iloc[-1]
            
            if current_price > sma_20 > sma_50 > sma_200:
                trend = 'STRONG_BULLISH'
                strength = 0.9
            elif current_price > sma_20 > sma_50:
                trend = 'BULLISH'
                strength = 0.7
            elif current_price < sma_20 < sma_50 < sma_200:
                trend = 'STRONG_BEARISH'
                strength = 0.9
            elif current_price < sma_20 < sma_50:
                trend = 'BEARISH'
                strength = 0.7
            else:
                trend = 'SIDEWAYS'
                strength = 0.5
            
            return {
                'direction': trend,
                'strength': strength,
                'current_price': float(current_price),
                'sma_20': float(sma_20),
                'sma_50': float(sma_50),
                'sma_200': float(sma_200)
            }
        except Exception as e:
            logger.error(f"Erro ao identificar tendência: {e}")
            return {}
    
    def _find_support_resistance(self, df: pd.DataFrame, window: int = 50) -> Dict:
        """Identifica níveis de suporte e resistência"""
        try:
            recent_data = df.tail(window)
            
            # Encontrar máximas e mínimas locais
            highs = recent_data['high'].nlargest(5).values
            lows = recent_data['low'].nsmallest(5).values
            
            resistance_levels = sorted(set(np.round(highs, 2)), reverse=True)[:3]
            support_levels = sorted(set(np.round(lows, 2)))[:3]
            
            return {
                'resistance': [float(r) for r in resistance_levels],
                'support': [float(s) for s in support_levels],
                'current_price': float(df['close'].iloc[-1])
            }
        except Exception as e:
            logger.error(f"Erro ao encontrar suporte/resistência: {e}")
            return {}
    
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict:
        """Analisa volatilidade do mercado"""
        try:
            atr = df['atr'].iloc[-1]
            volatility = df['volatility'].iloc[-1]
            bb_width = df['bb_width'].iloc[-1]
            
            # Classificar volatilidade
            avg_atr = df['atr'].tail(50).mean()
            
            if atr > avg_atr * 1.5:
                level = 'HIGH'
            elif atr < avg_atr * 0.5:
                level = 'LOW'
            else:
                level = 'NORMAL'
            
            return {
                'atr': float(atr),
                'volatility': float(volatility),
                'bb_width': float(bb_width),
                'level': level,
                'avg_atr_50': float(avg_atr)
            }
        except Exception as e:
            logger.error(f"Erro ao analisar volatilidade: {e}")
            return {}
    
    def _analyze_volume(self, df: pd.DataFrame) -> Dict:
        """Analisa perfil de volume"""
        try:
            current_volume = df['tick_volume'].iloc[-1]
            avg_volume = df['volume_sma'].iloc[-1]
            volume_ratio = df['volume_ratio'].iloc[-1]
            
            if volume_ratio > 1.5:
                activity = 'HIGH'
            elif volume_ratio < 0.5:
                activity = 'LOW'
            else:
                activity = 'NORMAL'
            
            return {
                'current_volume': int(current_volume),
                'average_volume': float(avg_volume),
                'volume_ratio': float(volume_ratio),
                'activity_level': activity
            }
        except Exception as e:
            logger.error(f"Erro ao analisar volume: {e}")
            return {}
    
    def _find_best_hours(self, df: pd.DataFrame) -> Dict:
        """Identifica melhores horários para trading"""
        try:
            df['hour'] = df.index.hour
            df['price_change'] = df['close'].pct_change().abs()
            
            hourly_stats = df.groupby('hour').agg({
                'price_change': ['mean', 'std'],
                'tick_volume': 'mean'
            })
            
            # Top 3 horas com maior movimento
            best_hours = hourly_stats.nlargest(3, ('price_change', 'mean')).index.tolist()
            
            return {
                'best_hours': [int(h) for h in best_hours],
                'hourly_volatility': hourly_stats[('price_change', 'mean')].to_dict()
            }
        except Exception as e:
            logger.error(f"Erro ao encontrar melhores horários: {e}")
            return {}
    
    def _calculate_win_rates(self, symbol: str, days: int) -> Dict:
        """Calcula taxas de vitória por direção"""
        try:
            trades = self.get_historical_trades(symbol, days)
            
            if not trades:
                return {'buy': 0.5, 'sell': 0.5, 'total_trades': 0}
            
            buy_trades = [t for t in trades if t['type'] == 'BUY']
            sell_trades = [t for t in trades if t['type'] == 'SELL']
            
            buy_wins = len([t for t in buy_trades if t['profit'] > 0])
            sell_wins = len([t for t in sell_trades if t['profit'] > 0])
            
            buy_rate = buy_wins / len(buy_trades) if buy_trades else 0.5
            sell_rate = sell_wins / len(sell_trades) if sell_trades else 0.5
            
            return {
                'buy': round(buy_rate, 3),
                'sell': round(sell_rate, 3),
                'total_trades': len(trades),
                'buy_trades': len(buy_trades),
                'sell_trades': len(sell_trades)
            }
        except Exception as e:
            logger.error(f"Erro ao calcular win rates: {e}")
            return {'buy': 0.5, 'sell': 0.5, 'total_trades': 0}
    
    def get_account_info(self) -> Optional[Dict]:
        """Obtém informações da conta MT5"""
        if not self.ensure_connection():
            return None
        
        try:
            account = mt5.account_info()
            if account is None:
                return None
            
            return {
                'login': account.login,
                'balance': account.balance,
                'equity': account.equity,
                'margin': account.margin,
                'margin_free': account.margin_free,
                'margin_level': account.margin_level,
                'profit': account.profit,
                'currency': account.currency,
                'leverage': account.leverage,
                'server': account.server
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações da conta: {e}")
            return None
