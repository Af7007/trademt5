"""
Serviço para gerenciar configurações de símbolos
"""
import sqlite3
from typing import Dict, List, Optional
from datetime import datetime

DB_PATH = "mlp_data.db"

class SymbolsConfigService:
    """Serviço para consultar e gerenciar configurações de símbolos"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
    
    def get_symbol_config(self, symbol: str) -> Optional[Dict]:
        """Obtém configuração de um símbolo específico"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM symbols_config 
            WHERE symbol = ? AND is_active = 1
        """, (symbol,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_active_symbols(self) -> List[Dict]:
        """Obtém todos os símbolos ativos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM symbols_config 
            WHERE is_active = 1
            ORDER BY symbol
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_recommended_config(self, symbol: str) -> Optional[Dict]:
        """Obtém configurações recomendadas para trading"""
        config = self.get_symbol_config(symbol)
        if not config:
            return None
        
        return {
            'symbol': config['symbol'],
            'timeframe': config['recommended_timeframe'],
            'lot_size': config['recommended_lot_size'],
            'tp_points': config['recommended_tp_points'],
            'sl_points': config['recommended_sl_points'],
            'tp_distance': config['tp_distance_for_50cents'],
            'sl_distance': config['sl_distance_for_1dollar'],
            'max_positions': config['max_positions_recommended'],
            'spread_typical': config['spread_typical'],
            'commission': config['commission_per_lot']
        }
    
    def is_market_open(self, symbol: str, check_time: datetime = None) -> bool:
        """Verifica se o mercado está aberto para o símbolo"""
        if check_time is None:
            check_time = datetime.utcnow()
        
        config = self.get_symbol_config(symbol)
        if not config:
            return False
        
        # Obter dia da semana (0=Monday, 6=Sunday)
        weekday = check_time.weekday()
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_name = day_names[weekday]
        
        # Obter horário de mercado para o dia
        market_hours_key = f'market_hours_{day_name}'
        market_hours = config.get(market_hours_key)
        
        if not market_hours or market_hours == 'None':
            return False
        
        # Parse horário (formato: HH:MM-HH:MM)
        try:
            start_str, end_str = market_hours.split('-')
            start_hour, start_min = map(int, start_str.split(':'))
            end_hour, end_min = map(int, end_str.split(':'))
            
            current_time = check_time.hour * 60 + check_time.minute
            start_time = start_hour * 60 + start_min
            end_time = end_hour * 60 + end_min
            
            return start_time <= current_time <= end_time
        except:
            return False
    
    def get_trading_costs(self, symbol: str, lot_size: float = 0.01) -> Dict:
        """Calcula custos de trading para um símbolo"""
        config = self.get_symbol_config(symbol)
        if not config:
            return {}
        
        spread_cost = config['spread_typical'] * config['point'] * lot_size * config['tick_value']
        commission = config['commission_per_lot'] * lot_size
        
        return {
            'spread_points': config['spread_typical'],
            'spread_cost_usd': spread_cost,
            'commission_usd': commission,
            'total_cost_usd': spread_cost + commission,
            'swap_long': config['swap_long'],
            'swap_short': config['swap_short']
        }
    
    def update_symbol_config(self, symbol: str, updates: Dict) -> bool:
        """Atualiza configuração de um símbolo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Construir query de update
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        # Adicionar updated_at
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        
        # Adicionar symbol ao final
        values.append(symbol)
        
        query = f"""
            UPDATE symbols_config 
            SET {', '.join(set_clauses)}
            WHERE symbol = ?
        """
        
        try:
            cursor.execute(query, values)
            conn.commit()
            success = cursor.rowcount > 0
        except Exception as e:
            print(f"Erro ao atualizar símbolo: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    def add_symbol_config(self, config: Dict) -> bool:
        """Adiciona nova configuração de símbolo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO symbols_config (
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
            """, config)
            conn.commit()
            success = True
        except Exception as e:
            print(f"Erro ao adicionar símbolo: {e}")
            success = False
        finally:
            conn.close()
        
        return success


# Instância global
symbols_config_service = SymbolsConfigService()


# Funções de conveniência
def get_symbol_config(symbol: str) -> Optional[Dict]:
    """Obtém configuração de um símbolo"""
    return symbols_config_service.get_symbol_config(symbol)


def get_recommended_config(symbol: str) -> Optional[Dict]:
    """Obtém configurações recomendadas para trading"""
    return symbols_config_service.get_recommended_config(symbol)


def is_market_open(symbol: str) -> bool:
    """Verifica se o mercado está aberto"""
    return symbols_config_service.is_market_open(symbol)


def get_trading_costs(symbol: str, lot_size: float = 0.01) -> Dict:
    """Calcula custos de trading"""
    return symbols_config_service.get_trading_costs(symbol, lot_size)
