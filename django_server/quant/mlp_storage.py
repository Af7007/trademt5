"""
Sistema de armazenamento MLP simples baseado em JSON
Resolve o problema de restart e torna o sistema sempre funcional
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from threading import RLock


class MLPJSONStorage:
    """
    Armazenamento simples para dados MLP usando JSON files
    """

    def __init__(self, base_path: str = "mlp_data"):
        self.base_path = base_path
        self._lock = RLock()
        os.makedirs(base_path, exist_ok=True)
        self._initialize_files()

        # Configurações padrão do bot
        self.default_bot_config = {
            'is_running': False,
            'confidence_threshold': 0.85,  # 85%
            'take_profit': 0.50,  # $0.50
            'operation_interval': 60,  # 60 segundos
            'last_operation_time': None,
            'auto_trading_enabled': False,
            'symbol': 'BTCUSDc'
        }

    def _initialize_files(self):
        """Inicializa arquivos se não existirem"""
        self.analyses_file = os.path.join(self.base_path, "analyses.json")
        self.trades_file = os.path.join(self.base_path, "trades.json")
        self.daily_stats_file = os.path.join(self.base_path, "daily_stats.json")

        # Cria arquivos vazios se não existir
        for file_path in [self.analyses_file, self.trades_file, self.daily_stats_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)

    def _load_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Carrega dados do arquivo JSON"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, file_path: str, data: List[Dict[str, Any]]):
        """Salva dados no arquivo JSON"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def save_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """
        Salva uma análise MLP
        """
        with self._lock:
            analyses = self._load_json(self.analyses_file)

            # Adiciona ID e timestamp se não existir
            analysis_id = len(analyses) + 1
            analysis_data['id'] = analysis_id
            analysis_data['timestamp'] = datetime.now().isoformat()

            analyses.append(analysis_data)
            self._save_json(self.analyses_file, analyses)

            print(f"[INFO] Analise MLP salva: ID {analysis_id}")
            return analysis_id

    def save_trade(self, trade_data: Dict[str, Any]) -> int:
        """
        Salva um trade MLP
        """
        with self._lock:
            trades = self._load_json(self.trades_file)

            # Adiciona ID e timestamp
            trade_id = len(trades) + 1
            trade_data['id'] = trade_id
            trade_data['created_at'] = datetime.now().isoformat()

            trades.append(trade_data)
            self._save_json(self.trades_file, trades)

            print(f"[INFO] Trade MLP salvo: ID {trade_id}, Ticket {trade_data.get('ticket')}")
            return trade_id

    def update_trade_profit(self, ticket: int, profit: float, exit_price: float = None, exit_reason: str = None):
        """
        Atualiza o lucro de um trade
        """
        with self._lock:
            trades = self._load_json(self.trades_file)

            for trade in trades:
                if trade.get('ticket') == ticket:
                    trade['profit'] = profit
                    trade['exit_price'] = exit_price
                    trade['exit_reason'] = exit_reason
                    trade['exit_time'] = datetime.now().isoformat()
                    trade['updated_at'] = datetime.now().isoformat()
                    break

            self._save_json(self.trades_file, trades)
            print(f"[INFO] Trade {ticket} atualizado: P&L ${profit}")

    def get_analysis_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Recupera histórico de análises
        """
        with self._lock:
            analyses = self._load_json(self.analyses_file)

            if symbol and symbol != 'all':
                analyses = [a for a in analyses if a.get('symbol') == symbol]

            analyses.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return analyses[:limit]

    def get_trade_history(self, symbol: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """
        Recupera histórico de trades
        """
        with self._lock:
            trades = self._load_json(self.trades_file)

            # Filtrar por data (últimos N dias)
            cutoff_date = datetime.now() - timedelta(days=days)
            trades = [
                t for t in trades
                if datetime.fromisoformat(t['created_at']) >= cutoff_date
            ]

            if symbol and symbol != 'all':
                trades = [t for t in trades if t.get('symbol') == symbol]

            trades.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return trades

    def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Recupera estatísticas diárias calculadas dinamicamente
        """
        with self._lock:
            analyses = self._load_json(self.analyses_file)
            trades = self._load_json(self.trades_file)

            # Agrupar por data
            daily_stats = {}

            # Estatísticas de análises
            for analysis in analyses:
                date_str = datetime.fromisoformat(analysis['timestamp']).date().isoformat()

                if date_str not in daily_stats:
                    daily_stats[date_str] = {
                        'date': date_str,
                        'total_analyses': 0,
                        'buy_signals': 0,
                        'sell_signals': 0,
                        'hold_signals': 0,
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'total_profit': 0.0,
                    }

                daily_stats[date_str]['total_analyses'] += 1

                signal = analysis.get('signal', '')
                if signal == 'BUY':
                    daily_stats[date_str]['buy_signals'] += 1
                elif signal == 'SELL':
                    daily_stats[date_str]['sell_signals'] += 1
                else:
                    daily_stats[date_str]['hold_signals'] += 1

            # Estatísticas de trades
            for trade in trades:
                date_str = datetime.fromisoformat(trade['created_at']).date().isoformat()

                if date_str in daily_stats:
                    daily_stats[date_str]['total_trades'] += 1

                    profit = trade.get('profit', 0)
                    if profit != 0:  # Trade fechado
                        daily_stats[date_str]['total_profit'] += profit
                        if profit > 0:
                            daily_stats[date_str]['winning_trades'] += 1
                        else:
                            daily_stats[date_str]['losing_trades'] += 1

            # Calcular métricas e converter para lista
            result = []
            for date_key, stats in sorted(daily_stats.items()):
                stats_copy = stats.copy()

                # Calcular win rate
                if stats['total_trades'] > 0 and stats['total_trades'] > 0:
                    stats_copy['win_rate'] = round((stats['winning_trades'] / stats['total_trades']) * 100, 2)
                    stats_copy['avg_profit'] = round(stats['total_profit'] / stats['total_trades'], 4)

                result.append(stats_copy)

            return result[::-1]  # Mais recente primeiro

    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Resumo geral das estatísticas
        """
        with self._lock:
            analyses = self._load_json(self.analyses_file)
            trades = self._load_json(self.trades_file)

            total_analyses = len(analyses)
            total_trades = len(trades)

            winning_trades = len([t for t in trades if t.get('profit', 0) > 0])
            losing_trades = len([t for t in trades if t.get('profit', 0) < 0])

            total_profit = sum([t.get('profit', 0) for t in trades])

            return {
                'total_analyses': total_analyses,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_profit': round(total_profit, 4),
                'win_rate': round((winning_trades / max(total_trades, 1)) * 100, 2) if total_trades > 0 else 0,
                'avg_profit': round(total_profit / max(total_trades, 1), 4) if total_trades > 0 else 0,
            }

    def get_bot_config(self) -> Dict[str, Any]:
        """
        Carrega configurações do bot
        """
        bot_config_file = os.path.join(self.base_path, "bot_config.json")

        try:
            with open(bot_config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Retorna config padrão e salva
            self.save_bot_config(self.default_bot_config)
            return self.default_bot_config.copy()

    def save_bot_config(self, config: Dict[str, Any]):
        """
        Salva configurações do bot
        """
        bot_config_file = os.path.join(self.base_path, "bot_config.json")
        with open(bot_config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def update_bot_config(self, **kwargs):
        """
        Atualiza configurações específicas do bot
        """
        current_config = self.get_bot_config()
        current_config.update(kwargs)
        self.save_bot_config(current_config)
        print(f"[INFO] Configuração do bot atualizada: {kwargs}")

    def can_execute_trade(self) -> bool:
        """
        Verifica se pode executar trade baseado no intervalo entre operações
        """
        config = self.get_bot_config()

        if not config['is_running']:
            return False

        last_operation = config.get('last_operation_time')
        if last_operation is None:
            return True

        try:
            last_time = datetime.fromisoformat(last_operation)
            time_diff = (datetime.now() - last_time).total_seconds()
            return time_diff >= config['operation_interval']
        except:
            return True

    def update_last_operation_time(self):
        """
        Atualiza timestamp da última operação
        """
        self.update_bot_config(last_operation_time=datetime.now().isoformat())


# Instância global
json_storage = MLPJSONStorage()
