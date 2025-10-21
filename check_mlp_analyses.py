"""
Script para verificar análises MLP no banco de dados
"""
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "mlp_data.db"

def check_analyses():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("="*80)
    print("  ANÁLISES MLP - ÚLTIMAS 20")
    print("="*80)
    
    # Buscar últimas 20 análises
    cursor.execute("""
        SELECT * FROM mlp_analyses 
        ORDER BY timestamp DESC 
        LIMIT 20
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("\nNenhuma análise encontrada no banco de dados.")
        conn.close()
        return
    
    print(f"\nTotal de análises: {len(rows)}\n")
    
    # Contar sinais
    signals_count = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
    
    for row in rows:
        timestamp = row['timestamp']
        symbol = row['symbol']
        signal = row['signal']
        confidence = row['confidence'] * 100
        
        signals_count[signal] = signals_count.get(signal, 0) + 1
        
        # Parsear indicadores (JSON)
        import json
        try:
            indicators = json.loads(row['indicators']) if row['indicators'] else {}
            market = json.loads(row['market_conditions']) if row['market_conditions'] else {}
            market_data = json.loads(row['market_data']) if row['market_data'] else {}
        except:
            indicators = {}
            market = {}
            market_data = {}
        
        rsi = indicators.get('rsi', 0)
        trend = market.get('trend', 'N/A')
        price = market_data.get('close', 0)
        
        # Cor do sinal
        signal_display = signal
        if signal == 'BUY':
            signal_display = f"\033[92m{signal}\033[0m"  # Verde
        elif signal == 'SELL':
            signal_display = f"\033[91m{signal}\033[0m"  # Vermelho
        else:
            signal_display = f"\033[90m{signal}\033[0m"  # Cinza
        
        print(f"{timestamp} | {symbol:10} | {signal_display:4} | {confidence:5.1f}% | RSI: {rsi:5.1f} | Trend: {trend:8} | Price: {price:.2f}")
    
    print("\n" + "="*80)
    print("  RESUMO DOS SINAIS")
    print("="*80)
    print(f"BUY:  {signals_count.get('BUY', 0):3} ({signals_count.get('BUY', 0)/len(rows)*100:.1f}%)")
    print(f"SELL: {signals_count.get('SELL', 0):3} ({signals_count.get('SELL', 0)/len(rows)*100:.1f}%)")
    print(f"HOLD: {signals_count.get('HOLD', 0):3} ({signals_count.get('HOLD', 0)/len(rows)*100:.1f}%)")
    
    # Verificar por símbolo
    print("\n" + "="*80)
    print("  ANÁLISES POR SÍMBOLO")
    print("="*80)
    
    cursor.execute("""
        SELECT symbol, signal, COUNT(*) as count
        FROM mlp_analyses
        WHERE timestamp > datetime('now', '-1 hour')
        GROUP BY symbol, signal
        ORDER BY symbol, signal
    """)
    
    symbol_stats = cursor.fetchall()
    
    if symbol_stats:
        print("\nÚltima hora:")
        current_symbol = None
        for row in symbol_stats:
            if current_symbol != row['symbol']:
                if current_symbol:
                    print()
                current_symbol = row['symbol']
                print(f"\n{current_symbol}:")
            print(f"  {row['signal']:4}: {row['count']:3} análises")
    
    conn.close()

if __name__ == "__main__":
    check_analyses()
