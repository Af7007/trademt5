"""
MLP Storage - Sistema independente de armazenagem para Flask
Substitui dependências de Django ORM por arquivos JSON locais
Versão completa e independente para commit
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

class MLPStorage:
    """Classe de storage independente MLP usando JSON"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent / "data"
        self.base_dir.mkdir(exist_ok=True)

        self.analyses_file = self.base_dir / "analyses.json"
        self.trades_file = self.base_dir / "trades.json"
        self.daily_stats_file = self.base_dir / "daily_stats.json"
        self.bot_config_file = self.base_dir / "bot_config.json"

        # Inicializar arquivos se não existirem
        self._init_files()

    def _init_files(self):
        """Inicializa arquivos JSON se não existirem"""
        if not self.analyses_file.exists():
            self.analyses_file.write_text("[]")
        if not self.trades_file.exists():
            self.trades_file.write_text("[]")
        if not self.daily_stats_file.exists():
            self.daily_stats_file.write_text("[]")
        if not self.bot_config_file.exists():
            config = {
                "take_profit": 0.5,
                "confidence_threshold": 0.85,
                "auto_trading_enabled": False,
                "symbol": "BTCUSDc"
            }
            self.bot_config_file.write_text(json.dumps(config, indent=2))

    def get_analyses(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Obtém análises MLP filtradas"""
        try:
            with open(self.analyses_file, 'r') as f:
                analyses = json.load(f)

            # Filtrar por símbolo se especificado
            if symbol and symbol != 'all':
                analyses = [a for a in analyses if a.get('symbol') == symbol]

            # Ordenar por timestamp descendente
            analyses.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

            return analyses[:limit]

        except Exception as e:
            logger.error(f"Erro ao carregar análises: {e}")
            return []

    def add_analysis(self, analysis: Dict) -> bool:
        """Adiciona nova análise MLP"""
        try:
            analyses = self.get_analyses(limit=10000)  # Carregar todas

            # Adicionar nova análise
            analysis['id'] = max([a.get('id', 0) for a in analyses], default=0) + 1
            analysis['timestamp'] = datetime.now().isoformat()
            analyses.insert(0, analysis)  # Adicionar no início

            # Salvar
            with open(self.analyses_file, 'w') as f:
                json.dump(analyses, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar análise: {e}")
            return False

    def get_trades(self, symbol: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Obtém trades MLP filtrados por período"""
        try:
            with open(self.trades_file, 'r') as f:
                trades = json.load(f)

            # Filtrar por período
            cutoff_date = datetime.now() - timedelta(days=days)
            trades = [
                t for t in trades
                if datetime.fromisoformat(t.get('created_at', '2000-01-01').replace('Z', '+00:00')) >= cutoff_date
            ]

            # Filtrar por símbolo se especificado
            if symbol and symbol != 'all':
                trades = [t for t in trades if t.get('symbol') == symbol]

            # Ordenar por data descendente
            trades.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            return trades

        except Exception as e:
            logger.error(f"Erro ao carregar trades: {e}")
            return []

    def add_trade(self, trade: Dict) -> bool:
        """Adiciona novo trade MLP"""
        try:
            trades = self.get_trades(days=10000)  # Carregar todos

            # Adicionar novo trade
            trade['id'] = max([t.get('id', 0) for t in trades], default=0) + 1
            if 'created_at' not in trade:
                trade['created_at'] = datetime.now().isoformat()

            trades.insert(0, trade)  # Adicionar no início

            # Salvar
            with open(self.trades_file, 'w') as f:
                json.dump(trades, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar trade: {e}")
            return False

    def update_trade(self, ticket: int, updates: Dict) -> bool:
        """Atualiza trade existente"""
        try:
            trades = self.get_trades(days=10000)  # Carregar todos

            # Encontrar trade por ticket
            for trade in trades:
                if str(trade.get('ticket', '')) == str(ticket):
                    # Aplicar atualizações
                    trade.update(updates)
                    trade['exit_time'] = datetime.now().isoformat()

                    # Salvar
                    with open(self.trades_file, 'w') as f:
                        json.dump(trades, f, indent=2)

                    return True

            return False

        except Exception as e:
            logger.error(f"Erro ao atualizar trade: {e}")
            return False

    def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """Obtém estatísticas diárias MLP"""
        try:
            with open(self.daily_stats_file, 'r') as f:
                stats = json.load(f)

            # Filtrar por período
            cutoff_date = datetime.now() - timedelta(days=days)
            stats = [
                s for s in stats
                if datetime.fromisoformat(s.get('date', '2000-01-01')) >= cutoff_date
            ]

            # Ordenar por data descendente
            stats.sort(key=lambda x: x.get('date', ''), reverse=True)

            return stats

        except Exception as e:
            logger.error(f"Erro ao carregar estatísticas diárias: {e}")
            return []

    def add_daily_stats(self, stats: Dict) -> bool:
        """Adiciona estatísticas diárias"""
        try:
            daily_stats = self.get_daily_stats(days=1000)  # Carregar todos

            # Verificar se já existe para hoje
            today = datetime.now().date().isoformat()
            existing = None
            for s in daily_stats:
                if s.get('date') == today:
                    existing = s
                    break

            if existing:
                # Atualizar existente
                existing.update(stats)
            else:
                # Adicionar novo
                stats['date'] = today
                daily_stats.insert(0, stats)

            # Salvar
            with open(self.daily_stats_file, 'w') as f:
                json.dump(daily_stats, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar estatísticas diárias: {e}")
            return False

    def get_config(self) -> Dict:
        """Obtém configuração do bot MLP"""
        try:
            with open(self.bot_config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return {
                "take_profit": 0.5,
                "confidence_threshold": 0.85,
                "auto_trading_enabled": False,
                "symbol": "BTCUSDc"
            }

    def update_config(self, updates: Dict) -> bool:
        """Atualiza configuração do bot MLP"""
        try:
            config = self.get_config()
            config.update(updates)

            with open(self.bot_config_file, 'w') as f:
                json.dump(config, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")
            return False

# Instância global
mlp_storage = MLPStorage()
