from flask import Blueprint, jsonify, render_template
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from lib import get_positions
from pattern_analyzer import analyze_market

btcusd_stats_bp = Blueprint('btcusd_stats', __name__)

@btcusd_stats_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Render BTCUSD Dashboard HTML page (simple version)
    """
    return render_template('btcusd_dashboard.html')

@btcusd_stats_bp.route('/chart', methods=['GET'])
def chart():
    """
    Render BTCUSD Advanced Charts with Technical Indicators
    """
    return render_template('btcusd_modern.html')

@btcusd_stats_bp.route('/chart/classic', methods=['GET'])
def chart_classic():
    """
    Render BTCUSD Classic Chart
    """
    return render_template('btcusd_chart.html')

@btcusd_stats_bp.route('/btcusd/stats', methods=['GET'])
def get_btcusd_stats():
    """
    Get comprehensive BTCUSD statistics
    ---
    tags:
      - BTCUSD Dashboard
    responses:
      200:
        description: BTCUSD statistics
    """
    try:
        symbol = "BTCUSDc"

        # Initialize MT5
        if not mt5.initialize():
            return jsonify({"error": "MT5 initialization failed"}), 500

        # Get current tick data
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return jsonify({"error": f"Failed to get tick for {symbol}"}), 500

        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return jsonify({"error": f"Failed to get symbol info for {symbol}"}), 500

        # Get current positions
        positions_df = get_positions()
        btc_positions = positions_df[positions_df['symbol'] == symbol] if not positions_df.empty else pd.DataFrame()

        # Calculate position statistics
        total_positions = len(btc_positions)
        total_volume = btc_positions['volume'].sum() if not btc_positions.empty else 0.0
        total_profit = btc_positions['profit'].sum() if not btc_positions.empty else 0.0

        # Get historical data for analysis
        rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
        rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 24)
        rates_d1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 7)

        df_m1 = pd.DataFrame(rates_m1) if rates_m1 is not None else pd.DataFrame()
        df_h1 = pd.DataFrame(rates_h1) if rates_h1 is not None else pd.DataFrame()
        df_d1 = pd.DataFrame(rates_d1) if rates_d1 is not None else pd.DataFrame()

        # Calculate technical indicators on M1
        m1_stats = {}
        if not df_m1.empty:
            m1_stats = {
                "current_price": float(tick.ask),
                "high_100m": float(df_m1['high'].max()),
                "low_100m": float(df_m1['low'].min()),
                "avg_100m": float(df_m1['close'].mean()),
                "volatility_100m": float(df_m1['close'].std()),
                "last_close": float(df_m1['close'].iloc[-1]) if len(df_m1) > 0 else 0.0,
            }

        # Calculate hourly stats
        h1_stats = {}
        if not df_h1.empty:
            h1_stats = {
                "high_24h": float(df_h1['high'].max()),
                "low_24h": float(df_h1['low'].min()),
                "avg_24h": float(df_h1['close'].mean()),
                "change_24h": float(df_h1['close'].iloc[-1] - df_h1['close'].iloc[0]) if len(df_h1) > 1 else 0.0,
                "change_24h_pct": float(((df_h1['close'].iloc[-1] - df_h1['close'].iloc[0]) / df_h1['close'].iloc[0]) * 100) if len(df_h1) > 1 else 0.0,
            }

        # Calculate daily stats
        d1_stats = {}
        if not df_d1.empty:
            d1_stats = {
                "high_7d": float(df_d1['high'].max()),
                "low_7d": float(df_d1['low'].min()),
                "avg_7d": float(df_d1['close'].mean()),
                "change_7d": float(df_d1['close'].iloc[-1] - df_d1['close'].iloc[0]) if len(df_d1) > 1 else 0.0,
                "change_7d_pct": float(((df_d1['close'].iloc[-1] - df_d1['close'].iloc[0]) / df_d1['close'].iloc[0]) * 100) if len(df_d1) > 1 else 0.0,
            }

        # Build response
        response = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "tick": {
                "bid": float(tick.bid),
                "ask": float(tick.ask),
                "last": float(tick.last),
                "spread": float(tick.ask - tick.bid),
                "volume": int(tick.volume),
                "time": datetime.fromtimestamp(tick.time).isoformat(),
            },
            "symbol_info": {
                "digits": symbol_info.digits,
                "point": float(symbol_info.point),
                "spread": symbol_info.spread,
                "trade_contract_size": float(symbol_info.trade_contract_size),
                "volume_min": float(symbol_info.volume_min),
                "volume_max": float(symbol_info.volume_max),
                "volume_step": float(symbol_info.volume_step),
            },
            "positions": {
                "total": int(total_positions),
                "total_volume": float(total_volume),
                "total_profit": float(total_profit),
                "list": btc_positions.to_dict('records') if not btc_positions.empty else []
            },
            "stats_1m": m1_stats,
            "stats_1h": h1_stats,
            "stats_1d": d1_stats,
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@btcusd_stats_bp.route('/btcusd/candles/<timeframe>', methods=['GET'])
def get_btcusd_candles(timeframe):
    """
    Get BTCUSD candlestick data
    ---
    tags:
      - BTCUSD Dashboard
    parameters:
      - name: timeframe
        in: path
        type: string
        required: true
        description: Timeframe (M1, M5, M15, H1, H4, D1)
      - name: bars
        in: query
        type: integer
        default: 100
        description: Number of bars to retrieve
    responses:
      200:
        description: Candlestick data
    """
    from flask import request

    try:
        symbol = "BTCUSDc"
        num_bars = int(request.args.get('bars', 100))

        # Map timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }

        if timeframe not in timeframe_map:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Initialize MT5
        if not mt5.initialize():
            return jsonify({"error": "MT5 initialization failed"}), 500

        # Get data
        rates = mt5.copy_rates_from_pos(symbol, timeframe_map[timeframe], 0, num_bars)
        if rates is None:
            return jsonify({"error": "Failed to get rates data"}), 404

        df = pd.DataFrame(rates)

        if df.empty:
            return jsonify({"error": "No data available"}), 404

        # Convert to list of candles
        candles = []
        for idx, row in df.iterrows():
            # Convert timestamp to ISO format
            if isinstance(idx, (int, float)):
                # Convert Unix timestamp to datetime
                from datetime import datetime
                dt_time = datetime.fromtimestamp(idx)
                time_iso = dt_time.isoformat()
            else:
                # If it's already a datetime object
                time_iso = idx.isoformat()

            candles.append({
                "time": time_iso,
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['tick_volume']),
            })

        return jsonify({
            "symbol": symbol,
            "timeframe": timeframe,
            "bars": len(candles),
            "candles": candles
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@btcusd_stats_bp.route('/btcusd/analysis/<timeframe>', methods=['GET'])
def get_btcusd_analysis(timeframe):
    """
    Get comprehensive market analysis with patterns and entry signals
    ---
    tags:
      - BTCUSD Dashboard
    parameters:
      - name: timeframe
        in: path
        type: string
        required: true
        description: Timeframe (M1, M5, M15, H1, H4, D1)
    responses:
      200:
        description: Market analysis with patterns and signals
    """
    from flask import request

    try:
        symbol = "BTCUSDc"
        num_bars = 100  # Enough for pattern detection

        # Map timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }

        if timeframe not in timeframe_map:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Initialize MT5
        if not mt5.initialize():
            return jsonify({"error": "MT5 initialization failed"}), 500

        # Get data with extra bars for calculations
        rates = mt5.copy_rates_from_pos(symbol, timeframe_map[timeframe], 0, num_bars)
        if rates is None:
            return jsonify({"error": "Failed to get rates data"}), 404

        df = pd.DataFrame(rates)
        if df.empty:
            return jsonify({"error": "No data available"}), 404

        # Calculate indicators for analysis
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()

        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

        df['time'] = pd.to_datetime(df['time'], unit='s')
        df = df.set_index('time')

        # Run comprehensive analysis
        analysis = analyze_market(df)

        return jsonify({
            "symbol": symbol,
            "timeframe": timeframe,
            "analysis": analysis
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500




@btcusd_stats_bp.route('/btcusd/indicators/<timeframe>', methods=['GET'])
def get_btcusd_indicators(timeframe):
    """
    Get BTCUSD candlestick data with technical indicators
    ---
    tags:
      - BTCUSD Dashboard
    parameters:
      - name: timeframe
        in: path
        type: string
        required: true
        description: Timeframe (M1, M5, M15, H1, H4, D1)
      - name: bars
        in: query
        type: integer
        default: 100
        description: Number of bars to retrieve
    responses:
      200:
        description: Candlestick data with indicators
    """
    from flask import request

    try:
        print(f"[DEBUG] GET /btcusd/indicators/{timeframe} called")
        symbol = "BTCUSDc"
        num_bars = int(request.args.get('bars', 100))

        # Map timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }

        if timeframe not in timeframe_map:
            return jsonify({"error": f"Invalid timeframe: {timeframe}"}), 400

        # Initialize MT5
        if not mt5.initialize():
            return jsonify({"error": "MT5 initialization failed"}), 500

        # Get data
        rates = mt5.copy_rates_from_pos(symbol, timeframe_map[timeframe], 0, num_bars)
        if rates is None:
            return jsonify({"error": "Failed to get rates data"}), 404

        df = pd.DataFrame(rates)

        if df.empty:
            return jsonify({"error": "No data available"}), 404

        # Calculate technical indicators
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # MACD calculation
        df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # Convert to list of candles with indicators
        candles = []
        for idx, row in df.iterrows():
            # Convert timestamp to ISO format
            if isinstance(idx, (int, float)):
                # Convert Unix timestamp to datetime
                from datetime import datetime
                dt_time = datetime.fromtimestamp(idx)
                time_iso = dt_time.isoformat()
            else:
                # If it's already a datetime object
                time_iso = idx.isoformat()

            # Handle NaN values for indicators
            sma_20 = float(row['sma_20']) if pd.notna(row['sma_20']) else None
            sma_50 = float(row['sma_50']) if pd.notna(row['sma_50']) else None
            bb_upper = float(row['bb_upper']) if pd.notna(row['bb_upper']) else None
            bb_lower = float(row['bb_lower']) if pd.notna(row['bb_lower']) else None
            rsi = float(row['rsi']) if pd.notna(row['rsi']) else None
            macd = float(row['macd']) if pd.notna(row['macd']) else None
            macd_signal = float(row['macd_signal']) if pd.notna(row['macd_signal']) else None
            macd_histogram = float(row['macd_histogram']) if pd.notna(row['macd_histogram']) else None

            candles.append({
                "time": time_iso,
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['tick_volume']),
                "sma_20": sma_20,
                "sma_50": sma_50,
                "bb_upper": bb_upper,
                "bb_lower": bb_lower,
                "rsi": rsi,
                "macd": macd,
                "macd_signal": macd_signal,
                "macd_histogram": macd_histogram
            })

        return jsonify({
            "symbol": symbol,
            "timeframe": timeframe,
            "bars": len(candles),
            "candles": candles
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
