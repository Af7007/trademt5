"""
Cria tabela de configurações de símbolos no banco de dados
Armazena particularidades de cada token: horário de mercado, custos, spreads, etc.
"""
import sqlite3
from datetime import datetime

DB_PATH = "mlp_data.db"

def create_symbols_config_table():
    """Cria tabela de configurações de símbolos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symbols_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            
            -- Características do símbolo
            digits INTEGER NOT NULL,
            point REAL NOT NULL,
            tick_size REAL NOT NULL,
            tick_value REAL NOT NULL,
            contract_size REAL NOT NULL,
            
            -- Volumes
            volume_min REAL NOT NULL,
            volume_max REAL NOT NULL,
            volume_step REAL NOT NULL,
            
            -- Custos de operação
            spread_typical INTEGER,
            spread_min INTEGER,
            spread_max INTEGER,
            commission_per_lot REAL DEFAULT 0.0,
            swap_long REAL DEFAULT 0.0,
            swap_short REAL DEFAULT 0.0,
            
            -- Stops
            stops_level INTEGER DEFAULT 0,
            freeze_level INTEGER DEFAULT 0,
            
            -- Horários de mercado (formato: HH:MM-HH:MM)
            market_hours_monday TEXT,
            market_hours_tuesday TEXT,
            market_hours_wednesday TEXT,
            market_hours_thursday TEXT,
            market_hours_friday TEXT,
            market_hours_saturday TEXT,
            market_hours_sunday TEXT,
            timezone TEXT DEFAULT 'UTC',
            
            -- Configurações de trading recomendadas
            recommended_timeframe TEXT DEFAULT 'M1',
            recommended_lot_size REAL DEFAULT 0.01,
            recommended_tp_points INTEGER,
            recommended_sl_points INTEGER,
            max_positions_recommended INTEGER DEFAULT 1,
            
            -- Cálculos para profit
            -- Para $0.50 de lucro com 0.01 lote
            tp_distance_for_50cents REAL,
            sl_distance_for_1dollar REAL,
            
            -- Metadados
            is_active BOOLEAN DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    print("✓ Tabela 'symbols_config' criada com sucesso!")
    
    conn.commit()
    conn.close()

def insert_default_symbols():
    """Insere configurações padrão para BTCUSDc e XAUUSDc"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    symbols_data = [
        {
            # BTCUSDc - Bitcoin
            'symbol': 'BTCUSDc',
            'name': 'Bitcoin vs US Dollar',
            'asset_type': 'Cryptocurrency',
            'digits': 2,
            'point': 0.01,
            'tick_size': 0.01,
            'tick_value': 0.01,
            'contract_size': 0.01,
            'volume_min': 0.01,
            'volume_max': 1000.0,
            'volume_step': 0.01,
            'spread_typical': 1800,
            'spread_min': 1000,
            'spread_max': 3000,
            'commission_per_lot': 0.0,
            'swap_long': 0.0,
            'swap_short': 0.0,
            'stops_level': 0,
            'freeze_level': 0,
            'market_hours_monday': '00:00-23:59',
            'market_hours_tuesday': '00:00-23:59',
            'market_hours_wednesday': '00:00-23:59',
            'market_hours_thursday': '00:00-23:59',
            'market_hours_friday': '00:00-23:59',
            'market_hours_saturday': '00:00-23:59',
            'market_hours_sunday': '00:00-23:59',
            'timezone': 'UTC',
            'recommended_timeframe': 'M1',
            'recommended_lot_size': 0.01,
            'recommended_tp_points': 5000,
            'recommended_sl_points': 10000,
            'max_positions_recommended': 1,
            'tp_distance_for_50cents': 50.0,
            'sl_distance_for_1dollar': 100.0,
            'is_active': 1,
            'notes': 'Bitcoin - Mercado 24/7. Para $0.50 com 0.01 lote: TP=50.0 (5000 pontos), SL=100.0 (10000 pontos)'
        },
        {
            # XAUUSDc - Gold
            'symbol': 'XAUUSDc',
            'name': 'Gold vs US Dollar',
            'asset_type': 'Commodity',
            'digits': 3,
            'point': 0.001,
            'tick_size': 0.001,
            'tick_value': 0.1,
            'contract_size': 1.0,
            'volume_min': 0.01,
            'volume_max': 200.0,
            'volume_step': 0.01,
            'spread_typical': 160,
            'spread_min': 100,
            'spread_max': 300,
            'commission_per_lot': 0.0,
            'swap_long': -2.5,
            'swap_short': -1.5,
            'stops_level': 0,
            'freeze_level': 0,
            'market_hours_monday': '00:00-23:00',
            'market_hours_tuesday': '00:00-23:00',
            'market_hours_wednesday': '00:00-23:00',
            'market_hours_thursday': '00:00-23:00',
            'market_hours_friday': '00:00-21:00',
            'market_hours_saturday': None,
            'market_hours_sunday': '22:00-23:59',
            'timezone': 'UTC',
            'recommended_timeframe': 'M1',
            'recommended_lot_size': 0.01,
            'recommended_tp_points': 500,
            'recommended_sl_points': 1000,
            'max_positions_recommended': 1,
            'tp_distance_for_50cents': 0.5,
            'sl_distance_for_1dollar': 1.0,
            'is_active': 1,
            'notes': 'Ouro - Mercado fecha fim de semana. Para $0.50 com 0.01 lote: TP=0.5 (500 pontos), SL=1.0 (1000 pontos)'
        }
    ]
    
    for data in symbols_data:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO symbols_config (
                    symbol, name, asset_type, digits, point, tick_size, tick_value,
                    contract_size, volume_min, volume_max, volume_step,
                    spread_typical, spread_min, spread_max, commission_per_lot,
                    swap_long, swap_short, stops_level, freeze_level,
                    market_hours_monday, market_hours_tuesday, market_hours_wednesday,
                    market_hours_thursday, market_hours_friday, market_hours_saturday,
                    market_hours_sunday, timezone, recommended_timeframe,
                    recommended_lot_size, recommended_tp_points, recommended_sl_points,
                    max_positions_recommended, tp_distance_for_50cents,
                    sl_distance_for_1dollar, is_active, notes
                ) VALUES (
                    :symbol, :name, :asset_type, :digits, :point, :tick_size, :tick_value,
                    :contract_size, :volume_min, :volume_max, :volume_step,
                    :spread_typical, :spread_min, :spread_max, :commission_per_lot,
                    :swap_long, :swap_short, :stops_level, :freeze_level,
                    :market_hours_monday, :market_hours_tuesday, :market_hours_wednesday,
                    :market_hours_thursday, :market_hours_friday, :market_hours_saturday,
                    :market_hours_sunday, :timezone, :recommended_timeframe,
                    :recommended_lot_size, :recommended_tp_points, :recommended_sl_points,
                    :max_positions_recommended, :tp_distance_for_50cents,
                    :sl_distance_for_1dollar, :is_active, :notes
                )
            """, data)
            print(f"✓ Configuração inserida: {data['symbol']} - {data['name']}")
        except Exception as e:
            print(f"✗ Erro ao inserir {data['symbol']}: {e}")
    
    conn.commit()
    conn.close()

def show_symbols_config():
    """Mostra todas as configurações de símbolos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM symbols_config ORDER BY symbol")
    rows = cursor.fetchall()
    
    if not rows:
        print("Nenhuma configuração encontrada.")
        conn.close()
        return
    
    # Obter nomes das colunas
    columns = [description[0] for description in cursor.description]
    
    print("\n" + "="*100)
    print("  CONFIGURAÇÕES DE SÍMBOLOS")
    print("="*100)
    
    for row in rows:
        data = dict(zip(columns, row))
        print(f"\n{'='*100}")
        print(f"  {data['symbol']} - {data['name']}")
        print(f"{'='*100}")
        print(f"Tipo: {data['asset_type']}")
        print(f"\nCaracterísticas:")
        print(f"  Digits: {data['digits']}, Point: {data['point']}, Tick Size: {data['tick_size']}")
        print(f"  Tick Value: {data['tick_value']}, Contract Size: {data['contract_size']}")
        print(f"\nVolumes:")
        print(f"  Min: {data['volume_min']}, Max: {data['volume_max']}, Step: {data['volume_step']}")
        print(f"\nCustos:")
        print(f"  Spread: {data['spread_min']}-{data['spread_max']} (típico: {data['spread_typical']})")
        print(f"  Comissão: ${data['commission_per_lot']}/lote")
        print(f"  Swap Long: {data['swap_long']}, Swap Short: {data['swap_short']}")
        print(f"\nStops:")
        print(f"  Stops Level: {data['stops_level']}, Freeze Level: {data['freeze_level']}")
        print(f"\nHorários de Mercado ({data['timezone']}):")
        print(f"  Segunda: {data['market_hours_monday']}")
        print(f"  Terça: {data['market_hours_tuesday']}")
        print(f"  Quarta: {data['market_hours_wednesday']}")
        print(f"  Quinta: {data['market_hours_thursday']}")
        print(f"  Sexta: {data['market_hours_friday']}")
        print(f"  Sábado: {data['market_hours_saturday'] or 'Fechado'}")
        print(f"  Domingo: {data['market_hours_sunday'] or 'Fechado'}")
        print(f"\nConfigurações Recomendadas:")
        print(f"  Timeframe: {data['recommended_timeframe']}")
        print(f"  Lote: {data['recommended_lot_size']}")
        print(f"  TP: {data['recommended_tp_points']} pontos")
        print(f"  SL: {data['recommended_sl_points']} pontos")
        print(f"  Max Posições: {data['max_positions_recommended']}")
        print(f"\nPara Lucro de $0.50 (0.01 lote):")
        print(f"  TP Distance: {data['tp_distance_for_50cents']} em preço")
        print(f"  SL Distance: {data['sl_distance_for_1dollar']} em preço")
        print(f"\nStatus: {'Ativo' if data['is_active'] else 'Inativo'}")
        print(f"Notas: {data['notes']}")
        print(f"Criado: {data['created_at']}")
        print(f"Atualizado: {data['updated_at']}")
    
    print("\n" + "="*100)
    
    conn.close()

def main():
    print("="*100)
    print("  CRIAÇÃO DE TABELA DE CONFIGURAÇÕES DE SÍMBOLOS")
    print("="*100)
    
    # Criar tabela
    create_symbols_config_table()
    print()
    
    # Inserir dados padrão
    print("Inserindo configurações padrão...")
    insert_default_symbols()
    print()
    
    # Mostrar configurações
    show_symbols_config()
    
    print("\n✓ Tabela criada e populada com sucesso!")
    print("\nPara adicionar mais símbolos, use a função insert_symbol_config()")
    print("Para consultar: SELECT * FROM symbols_config WHERE symbol = 'BTCUSDc'")

if __name__ == "__main__":
    main()
