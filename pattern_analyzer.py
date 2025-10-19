"""
Pattern Analyzer for Candlestick and Market Analysis
Detects classic trading patterns and provides entry signals
"""

import pandas as pd
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CandlestickPatternAnalyzer:
    """Analyze candlestick patterns and market behavior"""

    @staticmethod
    def _validate_candle_data(candle, required_fields=['open', 'high', 'low', 'close']):
        """Validate that candle has required OHLC data"""
        if not isinstance(candle, pd.Series):
            logger.warning("Candle data is not a pandas Series")
            return False

        for field in required_fields:
            if field not in candle.index:
                logger.warning(f"Missing required field: {field}")
                return False
            if pd.isna(candle[field]):
                logger.warning(f"NaN value in field: {field}")
                return False

        return True

    @staticmethod
    def detect_hammer(candle):
        """
        Hammer: Bullish reversal pattern
        - Small body at top
        - Long lower shadow (2-3x body)
        - Little or no upper shadow
        """
        if not CandlestickPatternAnalyzer._validate_candle_data(candle):
            return False

        try:
            body = abs(candle['close'] - candle['open'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])

            if body == 0 or lower_shadow < 0 or upper_shadow < 0:
                return False

            return (
                lower_shadow >= body * 2 and
                upper_shadow <= body * 0.3 and
                candle['close'] > candle['open']  # Green candle preferred
            )
        except Exception as e:
            logger.error(f"Error detecting hammer pattern: {e}")
            return False

    @staticmethod
    def detect_inverted_hammer(candle):
        """
        Inverted Hammer: Bullish reversal at bottom
        - Small body at bottom
        - Long upper shadow
        - Little or no lower shadow
        """
        if not CandlestickPatternAnalyzer._validate_candle_data(candle):
            return False

        try:
            body = abs(candle['close'] - candle['open'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])

            if body == 0 or lower_shadow < 0 or upper_shadow < 0:
                return False

            return (
                upper_shadow >= body * 2 and
                lower_shadow <= body * 0.3
            )
        except Exception as e:
            logger.error(f"Error detecting inverted hammer pattern: {e}")
            return False

    @staticmethod
    def detect_shooting_star(candle):
        """
        Shooting Star: Bearish reversal at top
        - Small body at bottom
        - Long upper shadow
        - Little or no lower shadow
        """
        if not CandlestickPatternAnalyzer._validate_candle_data(candle):
            return False

        try:
            body = abs(candle['close'] - candle['open'])
            lower_shadow = min(candle['open'], candle['close']) - candle['low']
            upper_shadow = candle['high'] - max(candle['open'], candle['close'])

            if body == 0 or lower_shadow < 0 or upper_shadow < 0:
                return False

            return (
                upper_shadow >= body * 2 and
                lower_shadow <= body * 0.3 and
                candle['close'] < candle['open']  # Red candle preferred
            )
        except Exception as e:
            logger.error(f"Error detecting shooting star pattern: {e}")
            return False

    @staticmethod
    def detect_doji(candle):
        """
        Doji: Indecision pattern
        - Open equals close (or very close)
        - Can have long shadows
        """
        if not CandlestickPatternAnalyzer._validate_candle_data(candle):
            return False

        try:
            body = abs(candle['close'] - candle['open'])
            total_range = candle['high'] - candle['low']

            if total_range == 0 or body < 0:
                return False

            return body / total_range < 0.1
        except Exception as e:
            logger.error(f"Error detecting doji pattern: {e}")
            return False

    @staticmethod
    def detect_engulfing_bullish(prev_candle, curr_candle):
        """
        Bullish Engulfing: Strong reversal to upside
        - Previous candle is red
        - Current candle is green
        - Current body completely engulfs previous body
        """
        if not (CandlestickPatternAnalyzer._validate_candle_data(prev_candle) and
                CandlestickPatternAnalyzer._validate_candle_data(curr_candle)):
            return False

        try:
            prev_bearish = prev_candle['close'] < prev_candle['open']
            curr_bullish = curr_candle['close'] > curr_candle['open']

            curr_body_bigger = (
                curr_candle['close'] > prev_candle['open'] and
                curr_candle['open'] < prev_candle['close']
            )

            return prev_bearish and curr_bullish and curr_body_bigger
        except Exception as e:
            logger.error(f"Error detecting bullish engulfing pattern: {e}")
            return False

    @staticmethod
    def detect_engulfing_bearish(prev_candle, curr_candle):
        """
        Bearish Engulfing: Strong reversal to downside
        - Previous candle is green
        - Current candle is red
        - Current body completely engulfs previous body
        """
        if not (CandlestickPatternAnalyzer._validate_candle_data(prev_candle) and
                CandlestickPatternAnalyzer._validate_candle_data(curr_candle)):
            return False

        try:
            prev_bullish = prev_candle['close'] > prev_candle['open']
            curr_bearish = curr_candle['close'] < curr_candle['open']

            curr_body_bigger = (
                curr_candle['open'] > prev_candle['close'] and
                curr_candle['close'] < prev_candle['open']
            )

            return prev_bullish and curr_bearish and curr_body_bigger
        except Exception as e:
            logger.error(f"Error detecting bearish engulfing pattern: {e}")
            return False

    @staticmethod
    def detect_morning_star(candle1, candle2, candle3):
        """
        Morning Star: Bullish reversal (3 candles)
        - First: Long red candle
        - Second: Small body (doji-like)
        - Third: Long green candle
        """
        if not (CandlestickPatternAnalyzer._validate_candle_data(candle1) and
                CandlestickPatternAnalyzer._validate_candle_data(candle2) and
                CandlestickPatternAnalyzer._validate_candle_data(candle3)):
            return False

        try:
            first_bearish = candle1['close'] < candle1['open']
            second_small = abs(candle2['close'] - candle2['open']) < abs(candle1['close'] - candle1['open']) * 0.3
            third_bullish = candle3['close'] > candle3['open']

            third_recovers = candle3['close'] > (candle1['open'] + candle1['close']) / 2

            return first_bearish and second_small and third_bullish and third_recovers
        except Exception as e:
            logger.error(f"Error detecting morning star pattern: {e}")
            return False

    @staticmethod
    def detect_evening_star(candle1, candle2, candle3):
        """
        Evening Star: Bearish reversal (3 candles)
        - First: Long green candle
        - Second: Small body
        - Third: Long red candle
        """
        if not (CandlestickPatternAnalyzer._validate_candle_data(candle1) and
                CandlestickPatternAnalyzer._validate_candle_data(candle2) and
                CandlestickPatternAnalyzer._validate_candle_data(candle3)):
            return False

        try:
            first_bullish = candle1['close'] > candle1['open']
            second_small = abs(candle2['close'] - candle2['open']) < abs(candle1['close'] - candle1['open']) * 0.3
            third_bearish = candle3['close'] < candle3['open']

            third_drops = candle3['close'] < (candle1['open'] + candle1['close']) / 2

            return first_bullish and second_small and third_bearish and third_drops
        except Exception as e:
            logger.error(f"Error detecting evening star pattern: {e}")
            return False


class MarketBehaviorAnalyzer:
    """Analyze market behavior patterns"""

    @staticmethod
    def _validate_dataframe(df, min_length=10):
        """Validate DataFrame has required structure and data"""
        if df is None or df.empty:
            logger.warning("DataFrame is None or empty")
            return False

        if len(df) < min_length:
            logger.warning(f"Insufficient data: {len(df)} < {min_length}")
            return False

        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Missing required column: {col}")
                return False

        return True

    @staticmethod
    def detect_pump_and_dump(df, window=10):
        """
        Pump and Dump: Rapid increase followed by rapid decrease
        """
        if not MarketBehaviorAnalyzer._validate_dataframe(df, window):
            return False, None

        try:
            recent = df.tail(window)

            # Calculate price change
            start_price = recent.iloc[0]['close']
            max_price = recent['high'].max()
            end_price = recent.iloc[-1]['close']

            if start_price <= 0 or max_price <= 0:
                return False, None

            # Pump: >5% increase
            pump_pct = ((max_price - start_price) / start_price) * 100

            # Dump: drop from peak >3%
            dump_pct = ((max_price - end_price) / max_price) * 100

            is_pump_dump = pump_pct > 5 and dump_pct > 3

            return is_pump_dump, {
                'pump_pct': pump_pct,
                'dump_pct': dump_pct,
                'peak_price': max_price
            }
        except Exception as e:
            logger.error(f"Error detecting pump and dump pattern: {e}")
            return False, None

    @staticmethod
    def detect_accumulation(df, window=20):
        """
        Accumulation: Price consolidating in tight range with increasing volume
        """
        if not MarketBehaviorAnalyzer._validate_dataframe(df, window):
            return False, None

        try:
            recent = df.tail(window)

            # Price range
            price_range = (recent['high'].max() - recent['low'].min()) / recent['close'].mean()

            # Volume trend (check if tick_volume column exists)
            if 'tick_volume' not in recent.columns:
                logger.warning("tick_volume column not found for accumulation analysis")
                return False, None

            vol_first_half = recent.head(window // 2)['tick_volume'].mean()
            vol_second_half = recent.tail(window // 2)['tick_volume'].mean()

            if vol_first_half <= 0:
                return False, None

            volume_increasing = vol_second_half > vol_first_half * 1.2
            tight_range = price_range < 0.02  # Less than 2% range

            is_accumulation = tight_range and volume_increasing

            return is_accumulation, {
                'price_range_pct': price_range * 100,
                'volume_increase_pct': ((vol_second_half - vol_first_half) / vol_first_half) * 100
            }
        except Exception as e:
            logger.error(f"Error detecting accumulation pattern: {e}")
            return False, None

    @staticmethod
    def detect_breakout(df, window=20):
        """
        Breakout: Price breaking above resistance with volume
        """
        if not MarketBehaviorAnalyzer._validate_dataframe(df, window):
            return False, None

        try:
            recent = df.tail(window)
            last_candle = recent.iloc[-1]

            # Resistance level (recent high)
            resistance = recent.head(window - 1)['high'].max()

            # Volume comparison (check if tick_volume column exists)
            if 'tick_volume' not in last_candle.index:
                logger.warning("tick_volume column not found for breakout analysis")
                return False, None

            avg_volume = recent.head(window - 1)['tick_volume'].mean()
            current_volume = last_candle['tick_volume']

            if avg_volume <= 0:
                return False, None

            price_broke_resistance = last_candle['close'] > resistance
            volume_spike = current_volume > avg_volume * 1.5

            is_breakout = price_broke_resistance and volume_spike

            return is_breakout, {
                'resistance_level': resistance,
                'breakout_price': last_candle['close'],
                'volume_increase_pct': ((current_volume - avg_volume) / avg_volume) * 100
            }
        except Exception as e:
            logger.error(f"Error detecting breakout pattern: {e}")
            return False, None


class TrendAnalyzer:
    """Analyze market trend and generate entry signals"""

    @staticmethod
    def calculate_trend_strength(df):
        """
        Calculate trend strength based on multiple indicators
        Returns: score from -100 (strong bearish) to +100 (strong bullish)
        """
        if len(df) < 50:
            return 0

        last_candle = df.iloc[-1]
        score = 0

        # 1. Price vs Moving Averages (40 points)
        if 'sma_20' in last_candle and pd.notna(last_candle['sma_20']):
            if last_candle['close'] > last_candle['sma_20']:
                score += 20
            else:
                score -= 20

        if 'sma_50' in last_candle and pd.notna(last_candle['sma_50']):
            if last_candle['close'] > last_candle['sma_50']:
                score += 20
            else:
                score -= 20

        # 2. RSI (30 points)
        if 'rsi' in last_candle and pd.notna(last_candle['rsi']):
            rsi = last_candle['rsi']
            if rsi > 70:
                score -= 30  # Overbought
            elif rsi > 50:
                score += 15
            elif rsi > 30:
                score -= 15
            else:
                score += 30  # Oversold (reversal opportunity)

        # 3. MACD (30 points)
        if 'macd' in last_candle and 'macd_signal' in last_candle:
            if pd.notna(last_candle['macd']) and pd.notna(last_candle['macd_signal']):
                if last_candle['macd'] > last_candle['macd_signal']:
                    score += 15
                else:
                    score -= 15

                if last_candle['macd'] > 0:
                    score += 15
                else:
                    score -= 15

        return max(-100, min(100, score))

    @staticmethod
    def generate_entry_signal(df):
        """
        Generate entry signal: BUY, SELL, or HOLD
        Returns: (signal, confidence, reasons)
        """
        if len(df) < 50:
            return "HOLD", 0, ["Insufficient data"]

        trend_score = TrendAnalyzer.calculate_trend_strength(df)
        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2] if len(df) > 1 else None

        reasons = []
        signal = "HOLD"
        confidence = 0

        # Analyze trend
        if trend_score > 60:
            signal = "BUY"
            confidence = min(trend_score, 100)
            reasons.append(f"Strong bullish trend (score: {trend_score})")
        elif trend_score < -60:
            signal = "SELL"
            confidence = min(abs(trend_score), 100)
            reasons.append(f"Strong bearish trend (score: {trend_score})")
        else:
            confidence = 50
            reasons.append(f"Neutral trend (score: {trend_score})")

        # Check candlestick patterns
        analyzer = CandlestickPatternAnalyzer()

        if analyzer.detect_hammer(last_candle):
            if signal != "SELL":
                signal = "BUY"
                confidence = min(confidence + 20, 100)
                reasons.append("Hammer pattern detected (bullish reversal)")

        if analyzer.detect_shooting_star(last_candle):
            if signal != "BUY":
                signal = "SELL"
                confidence = min(confidence + 20, 100)
                reasons.append("Shooting Star detected (bearish reversal)")

        if prev_candle is not None:
            if analyzer.detect_engulfing_bullish(prev_candle, last_candle):
                signal = "BUY"
                confidence = min(confidence + 30, 100)
                reasons.append("Bullish Engulfing pattern (strong buy signal)")

            if analyzer.detect_engulfing_bearish(prev_candle, last_candle):
                signal = "SELL"
                confidence = min(confidence + 30, 100)
                reasons.append("Bearish Engulfing pattern (strong sell signal)")

        # RSI check
        if 'rsi' in last_candle and pd.notna(last_candle['rsi']):
            rsi = last_candle['rsi']
            if rsi < 30:
                if signal != "SELL":
                    signal = "BUY"
                    confidence = min(confidence + 15, 100)
                    reasons.append(f"RSI oversold ({rsi:.1f}) - possible reversal")
            elif rsi > 70:
                if signal != "BUY":
                    signal = "SELL"
                    confidence = min(confidence + 15, 100)
                    reasons.append(f"RSI overbought ({rsi:.1f}) - possible correction")

        return signal, confidence, reasons


def analyze_market(df):
    """
    Complete market analysis
    Returns comprehensive analysis including patterns, trends, and signals
    """
    try:
        # Validate input DataFrame
        if df is None or df.empty:
            return {'error': 'DataFrame is None or empty'}

        if len(df) < 3:
            return {'error': 'Insufficient data for analysis (minimum 3 candles required)'}

        # Ensure DataFrame has proper structure
        if not isinstance(df, pd.DataFrame):
            return {'error': 'Input must be a pandas DataFrame'}

        # Check for required columns
        required_columns = ['open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {'error': f'Missing required columns: {missing_columns}'}

        candle_analyzer = CandlestickPatternAnalyzer()
        market_analyzer = MarketBehaviorAnalyzer()
        trend_analyzer = TrendAnalyzer()

        # Safely get candle data
        try:
            last_candle = df.iloc[-1]
            prev_candle = df.iloc[-2]
            third_candle = df.iloc[-3] if len(df) > 2 else None
        except (IndexError, KeyError) as e:
            return {'error': f'Error accessing candle data: {e}'}

        # Detect candlestick patterns
        patterns_detected = []

        try:
            if candle_analyzer.detect_hammer(last_candle):
                patterns_detected.append({
                    'name': 'Hammer',
                    'type': 'bullish_reversal',
                    'description': 'Bullish reversal pattern at support'
                })

            if candle_analyzer.detect_shooting_star(last_candle):
                patterns_detected.append({
                    'name': 'Shooting Star',
                    'type': 'bearish_reversal',
                    'description': 'Bearish reversal pattern at resistance'
                })

            if candle_analyzer.detect_doji(last_candle):
                patterns_detected.append({
                    'name': 'Doji',
                    'type': 'indecision',
                    'description': 'Market indecision - trend may reverse'
                })

            if candle_analyzer.detect_engulfing_bullish(prev_candle, last_candle):
                patterns_detected.append({
                    'name': 'Bullish Engulfing',
                    'type': 'strong_bullish',
                    'description': 'Strong bullish reversal signal'
                })

            if candle_analyzer.detect_engulfing_bearish(prev_candle, last_candle):
                patterns_detected.append({
                    'name': 'Bearish Engulfing',
                    'type': 'strong_bearish',
                    'description': 'Strong bearish reversal signal'
                })

            if third_candle is not None:
                if candle_analyzer.detect_morning_star(third_candle, prev_candle, last_candle):
                    patterns_detected.append({
                        'name': 'Morning Star',
                        'type': 'strong_bullish',
                        'description': 'Three-candle bullish reversal pattern'
                    })

                if candle_analyzer.detect_evening_star(third_candle, prev_candle, last_candle):
                    patterns_detected.append({
                        'name': 'Evening Star',
                        'type': 'strong_bearish',
                        'description': 'Three-candle bearish reversal pattern'
                    })
        except Exception as e:
            logger.warning(f"Error detecting candlestick patterns: {e}")

        # Detect market behavior
        market_behaviors = []

        try:
            pump_dump, pump_details = market_analyzer.detect_pump_and_dump(df)
            if pump_dump and pump_details:
                market_behaviors.append({
                    'name': 'Pump and Dump',
                    'type': 'warning',
                    'description': f"Rapid rise (+{pump_details['pump_pct']:.1f}%) followed by dump (-{pump_details['dump_pct']:.1f}%)",
                    'details': pump_details
                })

            accumulation, acc_details = market_analyzer.detect_accumulation(df)
            if accumulation and acc_details:
                market_behaviors.append({
                    'name': 'Accumulation Phase',
                    'type': 'bullish',
                    'description': f"Price consolidating with volume increase (+{acc_details['volume_increase_pct']:.1f}%)",
                    'details': acc_details
                })

            breakout, break_details = market_analyzer.detect_breakout(df)
            if breakout and break_details:
                market_behaviors.append({
                    'name': 'Breakout',
                    'type': 'bullish',
                    'description': f"Price broke resistance ${break_details['resistance_level']:.2f} with volume surge",
                    'details': break_details
                })
        except Exception as e:
            logger.warning(f"Error detecting market behaviors: {e}")

        # Generate entry signal
        try:
            signal, confidence, reasons = trend_analyzer.generate_entry_signal(df)
            trend_score = trend_analyzer.calculate_trend_strength(df)
        except Exception as e:
            logger.error(f"Error generating entry signal: {e}")
            signal, confidence, reasons = "HOLD", 0, [f"Error in analysis: {e}"]
            trend_score = 0

        # Safely format timestamp
        try:
            timestamp = last_candle.name.isoformat() if hasattr(last_candle.name, 'isoformat') else str(last_candle.name)
        except:
            timestamp = "Unknown"

        return {
            'signal': signal,
            'confidence': confidence,
            'trend_score': trend_score,
            'reasons': reasons,
            'patterns': patterns_detected,
            'market_behavior': market_behaviors,
            'current_price': float(last_candle['close']),
            'timestamp': timestamp
        }

    except Exception as e:
        logger.error(f"Critical error in analyze_market: {e}")
        return {
            'error': f'Analysis failed: {str(e)}',
            'signal': 'HOLD',
            'confidence': 0,
            'trend_score': 0,
            'reasons': [f'Analysis error: {str(e)}'],
            'patterns': [],
            'market_behavior': []
        }
