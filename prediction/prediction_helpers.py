"""
Métodos auxiliares para o motor de predição
"""

import logging
import MetaTrader5 as mt5
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from .models import MarketAnalysis, TradeRecommendation, TradeDirection

logger = logging.getLogger(__name__)


class PredictionHelpers:
    """Métodos auxiliares para predição"""
    
    @staticmethod
    def analyze_market(data_collector, request) -> MarketAnalysis:
        """Analisa condições atuais do mercado"""
        try:
            timeframe = request.timeframe or 'M1'
            timeframe_mt5 = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }.get(timeframe, mt5.TIMEFRAME_M1)
            
            # Coletar dados históricos
            df = data_collector.get_historical_data(
                request.symbol, timeframe_mt5, 1000
            )
            
            if df is None:
                raise ValueError("Não foi possível obter dados históricos")
            
            # Calcular indicadores
            df = data_collector.calculate_indicators(df)
            
            # Analisar padrões
            patterns = data_collector.analyze_trading_patterns(
                request.symbol, timeframe_mt5, 30
            )
            
            # Obter indicadores mais recentes
            latest_indicators = {
                'rsi': float(df['rsi'].iloc[-1]),
                'macd': float(df['macd'].iloc[-1]),
                'macd_signal': float(df['signal'].iloc[-1]),
                'macd_histogram': float(df['macd_histogram'].iloc[-1]),
                'bb_position': PredictionHelpers._calculate_bb_position(df),
                'sma_20': float(df['sma_20'].iloc[-1]),
                'sma_50': float(df['sma_50'].iloc[-1]),
                'ema_12': float(df['ema_12'].iloc[-1]),
                'ema_26': float(df['ema_26'].iloc[-1]),
                'atr': float(df['atr'].iloc[-1]),
                'momentum': float(df['momentum'].iloc[-1]),
                'current_price': float(df['close'].iloc[-1])
            }
            
            return MarketAnalysis(
                symbol=request.symbol,
                timeframe=timeframe,
                trend=patterns.get('trend', {}),
                support_resistance=patterns.get('support_resistance', {}),
                volatility=patterns.get('volatility', {}),
                volume=patterns.get('volume_profile', {}),
                indicators=latest_indicators
            )
            
        except Exception as e:
            logger.error(f"Erro ao analisar mercado: {e}")
            raise
    
    @staticmethod
    def _calculate_bb_position(df) -> float:
        """Calcula posição do preço nas Bollinger Bands"""
        try:
            current_price = df['close'].iloc[-1]
            bb_upper = df['bb_upper'].iloc[-1]
            bb_lower = df['bb_lower'].iloc[-1]
            bb_middle = df['bb_middle'].iloc[-1]
            
            if current_price >= bb_middle:
                # Acima da média
                position = 0.5 + (0.5 * (current_price - bb_middle) / (bb_upper - bb_middle))
            else:
                # Abaixo da média
                position = 0.5 * (current_price - bb_lower) / (bb_middle - bb_lower)
            
            return round(float(position), 3)
        except:
            return 0.5
    
    @staticmethod
    def calculate_optimal_parameters(request, symbol_info, market_analysis) -> Dict:
        """Calcula parâmetros ótimos para trading"""
        try:
            # Calcular lote ótimo baseado no risco
            if request.lot_size is None:
                lot_size = PredictionHelpers._calculate_optimal_lot_size(
                    request.balance,
                    request.risk_percentage,
                    symbol_info,
                    market_analysis
                )
            else:
                lot_size = request.lot_size
            
            # Calcular TP e SL baseado na volatilidade
            atr = market_analysis.volatility.get('atr', 100)
            point = symbol_info['point']
            
            if request.take_profit is None:
                # TP baseado em 2x ATR
                take_profit_points = int((atr * 2) / point)
            else:
                take_profit_points = request.take_profit
            
            if request.stop_loss is None:
                # SL baseado em 1x ATR
                stop_loss_points = int(atr / point)
            else:
                stop_loss_points = request.stop_loss
            
            # Determinar melhor timeframe
            best_timeframe = PredictionHelpers._determine_best_timeframe(
                market_analysis,
                request.target_profit
            )
            
            return {
                'lot_size': lot_size,
                'take_profit': take_profit_points,
                'stop_loss': stop_loss_points,
                'best_timeframe': best_timeframe,
                'risk_reward_ratio': take_profit_points / stop_loss_points if stop_loss_points > 0 else 2.0
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular parâmetros ótimos: {e}")
            return {
                'lot_size': 0.01,
                'take_profit': 100,
                'stop_loss': 50,
                'best_timeframe': 'M1',
                'risk_reward_ratio': 2.0
            }
    
    @staticmethod
    def _calculate_optimal_lot_size(balance: float, risk_pct: float, 
                                     symbol_info: Dict, market_analysis) -> float:
        """Calcula tamanho ótimo do lote"""
        try:
            # Risco em dólares
            risk_amount = balance * (risk_pct / 100)
            
            # ATR em pontos
            atr = market_analysis.volatility.get('atr', 100)
            point = symbol_info['point']
            atr_points = atr / point
            
            # Valor por ponto
            tick_value = symbol_info['trade_tick_value']
            tick_size = symbol_info['trade_tick_size']
            point_value = tick_value / tick_size if tick_size > 0 else 1
            
            # Calcular lote
            lot_size = risk_amount / (atr_points * point_value)
            
            # Ajustar para limites do símbolo
            min_lot = symbol_info['volume_min']
            max_lot = symbol_info['volume_max']
            step = symbol_info['volume_step']
            
            lot_size = max(min_lot, min(lot_size, max_lot))
            lot_size = round(lot_size / step) * step
            
            return round(lot_size, 2)
            
        except Exception as e:
            logger.error(f"Erro ao calcular lote ótimo: {e}")
            return 0.01
    
    @staticmethod
    def _determine_best_timeframe(market_analysis, target_profit: float) -> str:
        """Determina o melhor timeframe baseado no objetivo"""
        try:
            volatility_level = market_analysis.volatility.get('level', 'NORMAL')
            trend_strength = market_analysis.trend.get('strength', 0.5)
            
            # Objetivo grande = timeframes maiores
            if target_profit > 100:
                if trend_strength > 0.7:
                    return 'H1'
                else:
                    return 'M15'
            elif target_profit > 50:
                if volatility_level == 'HIGH':
                    return 'M15'
                else:
                    return 'M5'
            else:
                # Alvos menores = timeframes menores
                return 'M1'
                
        except Exception as e:
            logger.error(f"Erro ao determinar timeframe: {e}")
            return 'M1'
    
    @staticmethod
    def generate_trade_recommendations(request, symbol_info, market_analysis, 
                                       optimal_params) -> List[TradeRecommendation]:
        """Gera recomendações de trade"""
        try:
            recommendations = []
            
            current_price = market_analysis.indicators['current_price']
            rsi = market_analysis.indicators['rsi']
            macd_histogram = market_analysis.indicators['macd_histogram']
            trend = market_analysis.trend.get('direction', 'SIDEWAYS')
            
            point = symbol_info['point']
            spread = symbol_info['spread'] * point
            
            # Analisar condições de compra
            buy_confidence = PredictionHelpers._calculate_buy_confidence(
                rsi, macd_histogram, trend, market_analysis
            )
            
            # Analisar condições de venda
            sell_confidence = PredictionHelpers._calculate_sell_confidence(
                rsi, macd_histogram, trend, market_analysis
            )
            
            # REGRA: Seguir a tendência dominante
            trend_strength = market_analysis.trend.get('strength', 0.5)
            
            # Se tendência forte (>70%), seguir apenas ela
            if trend_strength > 0.7:
                if 'BEARISH' in trend:
                    # Tendência de baixa forte: apenas SELL
                    buy_confidence = 0  # Anular compra
                elif 'BULLISH' in trend:
                    # Tendência de alta forte: apenas BUY
                    sell_confidence = 0  # Anular venda
            
            # Se ambas > 60%, escolher a maior
            if buy_confidence > 0.6 and sell_confidence > 0.6:
                if buy_confidence > sell_confidence:
                    sell_confidence = 0
                else:
                    buy_confidence = 0
            
            # Gerar recomendação de compra se confiança > 60%
            if buy_confidence > 0.6:
                tp_price = current_price + (optimal_params['take_profit'] * point)
                sl_price = current_price - (optimal_params['stop_loss'] * point)
                
                expected_profit = (tp_price - current_price - spread) * \
                                 symbol_info['trade_contract_size'] * \
                                 optimal_params['lot_size']
                expected_loss = (current_price - sl_price + spread) * \
                               symbol_info['trade_contract_size'] * \
                               optimal_params['lot_size']
                
                recommendations.append(TradeRecommendation(
                    direction=TradeDirection.BUY,
                    entry_price=current_price + spread,
                    stop_loss=sl_price,
                    take_profit=tp_price,
                    lot_size=optimal_params['lot_size'],
                    confidence=buy_confidence,
                    expected_profit=expected_profit,
                    expected_loss=abs(expected_loss),
                    risk_reward_ratio=optimal_params['risk_reward_ratio'],
                    reasoning=PredictionHelpers._generate_buy_reasoning(
                        rsi, macd_histogram, trend
                    ),
                    indicators=market_analysis.indicators
                ))
            
            # Gerar recomendação de venda se confiança > 60%
            if sell_confidence > 0.6:
                tp_price = current_price - (optimal_params['take_profit'] * point)
                sl_price = current_price + (optimal_params['stop_loss'] * point)
                
                expected_profit = (current_price - tp_price - spread) * \
                                 symbol_info['trade_contract_size'] * \
                                 optimal_params['lot_size']
                expected_loss = (sl_price - current_price + spread) * \
                               symbol_info['trade_contract_size'] * \
                               optimal_params['lot_size']
                
                recommendations.append(TradeRecommendation(
                    direction=TradeDirection.SELL,
                    entry_price=current_price,
                    stop_loss=sl_price,
                    take_profit=tp_price,
                    lot_size=optimal_params['lot_size'],
                    confidence=sell_confidence,
                    expected_profit=expected_profit,
                    expected_loss=abs(expected_loss),
                    risk_reward_ratio=optimal_params['risk_reward_ratio'],
                    reasoning=PredictionHelpers._generate_sell_reasoning(
                        rsi, macd_histogram, trend
                    ),
                    indicators=market_analysis.indicators
                ))
            
            return sorted(recommendations, key=lambda x: x.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
            return []
    
    @staticmethod
    def _calculate_buy_confidence(rsi, macd_histogram, trend, market_analysis) -> float:
        """Calcula confiança para compra"""
        confidence = 0.5  # Base
        
        # RSI oversold
        if rsi < 30:
            confidence += 0.2
        elif rsi < 50:
            confidence += 0.1
        
        # MACD positivo
        if macd_histogram > 0:
            confidence += 0.15
        
        # Trend bullish
        if 'BULLISH' in trend:
            confidence += 0.2
        
        # Volatilidade
        if market_analysis.volatility.get('level') == 'NORMAL':
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    @staticmethod
    def _calculate_sell_confidence(rsi, macd_histogram, trend, market_analysis) -> float:
        """Calcula confiança para venda"""
        confidence = 0.5  # Base
        
        # RSI overbought
        if rsi > 70:
            confidence += 0.2
        elif rsi > 50:
            confidence += 0.1
        
        # MACD negativo
        if macd_histogram < 0:
            confidence += 0.15
        
        # Trend bearish
        if 'BEARISH' in trend:
            confidence += 0.2
        
        # Volatilidade
        if market_analysis.volatility.get('level') == 'NORMAL':
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    @staticmethod
    def _generate_buy_reasoning(rsi, macd_histogram, trend) -> str:
        """Gera explicação para recomendação de compra"""
        reasons = []
        
        if rsi < 30:
            reasons.append("RSI em zona de sobrevenda (<30)")
        elif rsi < 50:
            reasons.append("RSI indicando força compradora")
        
        if macd_histogram > 0:
            reasons.append("MACD com histograma positivo")
        
        if 'BULLISH' in trend:
            reasons.append(f"Tendência de alta identificada ({trend})")
        
        if not reasons:
            reasons.append("Condições técnicas favoráveis")
        
        return ". ".join(reasons) + "."
    
    @staticmethod
    def _generate_sell_reasoning(rsi, macd_histogram, trend) -> str:
        """Gera explicação para recomendação de venda"""
        reasons = []
        
        if rsi > 70:
            reasons.append("RSI em zona de sobrecompra (>70)")
        elif rsi > 50:
            reasons.append("RSI indicando força vendedora")
        
        if macd_histogram < 0:
            reasons.append("MACD com histograma negativo")
        
        if 'BEARISH' in trend:
            reasons.append(f"Tendência de baixa identificada ({trend})")
        
        if not reasons:
            reasons.append("Condições técnicas favoráveis")
        
        return ". ".join(reasons) + "."
    
    @staticmethod
    def estimate_operations_and_time(request, market_analysis, optimal_params, symbol_info=None) -> Dict:
        """Estima número de operações e tempo necessário"""
        try:
            # Calcular lucro esperado por operação baseado no símbolo real
            lot_size = optimal_params['lot_size']
            tp_points = optimal_params['take_profit']
            sl_points = optimal_params['stop_loss']
            
            # Se temos symbol_info, calcular valores reais
            if symbol_info:
                point = symbol_info.get('point', 0.00001)
                contract_size = symbol_info.get('trade_contract_size', 100)
                
                # Lucro/Perda em valor monetário
                avg_win = (tp_points * point) * contract_size * lot_size
                avg_loss = (sl_points * point) * contract_size * lot_size
            else:
                # Fallback para estimativa conservadora
                avg_win = tp_points * lot_size * 10
                avg_loss = sl_points * lot_size * 10
            
            # Win rate estimado
            historical_patterns = market_analysis.trend
            base_win_rate = 0.55  # Base conservadora
            
            if historical_patterns.get('strength', 0) > 0.7:
                win_rate = 0.65
            else:
                win_rate = base_win_rate
            
            # Expectativa matemática por trade
            expectancy = (avg_win * win_rate) - (avg_loss * (1 - win_rate))
            
            if expectancy <= 0:
                expectancy = avg_win * 0.3  # Fallback conservador
            
            # Número de operações necessárias
            operations_needed = int(request.target_profit / expectancy) + 1
            
            # Limite se especificado
            if request.max_operations:
                operations_needed = min(operations_needed, request.max_operations)
            
            # Estimar tempo baseado no timeframe
            timeframe = optimal_params['best_timeframe']
            avg_trades_per_day = {
                'M1': 20,
                'M5': 15,
                'M15': 10,
                'M30': 8,
                'H1': 5,
                'H4': 3,
                'D1': 1
            }.get(timeframe, 10)
            
            days_needed = operations_needed / avg_trades_per_day
            hours_needed = days_needed * 24
            
            # Descrição
            if hours_needed < 1:
                description = f"Menos de 1 hora (aproximadamente {int(hours_needed * 60)} minutos)"
            elif hours_needed < 24:
                description = f"Aproximadamente {int(hours_needed)} horas"
            elif hours_needed < 168:
                description = f"Aproximadamente {int(days_needed)} dias"
            else:
                weeks = int(days_needed / 7)
                description = f"Aproximadamente {weeks} semanas"
            
            return {
                'operations': operations_needed,
                'duration_hours': round(hours_needed, 2),
                'description': description,
                'expectancy_per_trade': round(expectancy, 2),
                'win_rate': win_rate
            }
            
        except Exception as e:
            logger.error(f"Erro ao estimar operações: {e}")
            return {
                'operations': 10,
                'duration_hours': 24,
                'description': 'Aproximadamente 1 dia',
                'expectancy_per_trade': 10,
                'win_rate': 0.55
            }
