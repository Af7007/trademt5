#!/usr/bin/env python3
import sqlite3
import os

def check_database():
    db_path = os.path.join('mlp_data.db')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print('Tabelas encontradas:')
        for table in tables:
            print(f'  - {table[0]}')

        # Verificar análises
        cursor.execute('SELECT COUNT(*) FROM mlp_analyses')
        analyses_count = cursor.fetchone()[0]
        print(f'\nTotal de análises no banco: {analyses_count}')
        
        # Verificar trades
        cursor.execute('SELECT COUNT(*) FROM mlp_trades')
        trades_count = cursor.fetchone()[0]
        print(f'Total de trades no banco: {trades_count}')

        # Verificar trades sincronizados do MT5
        cursor.execute('SELECT COUNT(*) FROM mt5_trade_history')
        mt5_trades_count = cursor.fetchone()[0]
        print(f'Total de trades MT5 sincronizados: {mt5_trades_count}')

        # Verificar estatísticas diárias
        cursor.execute('SELECT COUNT(*) FROM mlp_daily_stats')
        daily_stats_count = cursor.fetchone()[0]
        print(f'Total de dias com estatísticas: {daily_stats_count}')

        # Mostrar últimas análises
        if analyses_count > 0:
            cursor.execute('SELECT id, symbol, signal, confidence, timestamp FROM mlp_analyses ORDER BY timestamp DESC LIMIT 3')
            analyses = cursor.fetchall()
            print('\nÚltimas análises:')
            for analysis in analyses:
                print(f'  - ID {analysis[0]}: {analysis[1]} {analysis[2]} (conf: {analysis[3]:.2f}) - {analysis[4]}')
        else:
            print('\nNenhuma análise encontrada no banco')

        conn.close()
    else:
        print('Banco mlp_data.db não encontrado')

if __name__ == "__main__":
    check_database()
