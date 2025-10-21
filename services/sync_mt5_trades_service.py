"""
MT5 Trade Synchronization Service
Serviço automático para sincronizar trades do MT5 com o banco SQLite
Executa em background e detecta novos trades (bot ou manuais) para atualização imediata
"""

import threading
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

import MetaTrader5 as mt5
from core.mt5_connection import mt5_connection
from services.mlp_storage import mlp_storage

logger = logging.getLogger(__name__)


class MT5TradeSyncService:
    """Serviço automático de sincronização de trades MT5 ↔ SQLite"""

    def __init__(self,
                 sync_interval: int = 60,  # Sincronizar a cada 60 segundos
                 lookback_days: int = 7,   # Verificar últimos 7 dias por padrão
                 auto_start: bool = False):
        """
        Initialize MT5 Trade Sync Service

        Args:
            sync_interval: Intervalo em segundos entre sincronizações
            lookback_days: Dias para verificar trades recentes
            auto_start: Se deve iniciar automaticamente
        """
        self.sync_interval = sync_interval
        self.lookback_days = lookback_days
        self.auto_start = auto_start

        # Estado do serviço
        self.is_running = False
        self.last_sync = None
        self.sync_stats = {
            'total_syncs': 0,
            'total_new_trades': 0,
            'last_error': None,
            'uptime_seconds': 0
        }

        # Controle de threads
        self.monitor_thread = None
        self.stop_flag = threading.Event()

        # Logger específico
        self.logger = logging.getLogger("MT5TradeSyncService")

    def start(self) -> bool:
        """Inicia o serviço de sincronização em background"""
        if self.is_running:
            self.logger.warning("MT5 Trade Sync Service já está rodando")
            return True

        try:
            self.logger.info(f"Iniciando MT5 Trade Sync Service - Interval: {self.sync_interval}s")

            # Verificar conexão inicial
            if not self._check_mt5_connection():
                self.logger.error("Não foi possível conectar ao MT5 - serviço não iniciado")
                return False

            self.is_running = True
            self.stop_flag.clear()
            self.last_sync = datetime.now()

            # Iniciar thread de monitoramento
            self.monitor_thread = threading.Thread(target=self._sync_loop,
                                                 name="MT5TradeSync",
                                                 daemon=True)
            self.monitor_thread.start()

            # Executar primeira sincronização imediata
            self.logger.info("Executando primeira sincronização...")
            sync_result = self.sync_now()
            if sync_result:
                self.logger.info(f"Sincronização inicial: {sync_result}")

            return True

        except Exception as e:
            self.logger.error(f"Erro ao iniciar MT5 Trade Sync Service: {e}")
            self.is_running = False
            return False

    def stop(self) -> bool:
        """Para o serviço de sincronização"""
        if not self.is_running:
            return True

        try:
            self.logger.info("Parando MT5 Trade Sync Service...")

            self.is_running = False
            self.stop_flag.set()

            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=10)  # Aguardar até 10s

            self.logger.info("MT5 Trade Sync Service parado")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao parar MT5 Trade Sync Service: {e}")
            return False

    def sync_now(self) -> Optional[Dict]:
        """Executa sincronização imediata e retorna resultado"""
        try:
            self.logger.info("Executando sincronização manual...")

            # Verificar MT5 conexão
            if not self._check_mt5_connection():
                return {"error": "MT5 não conectado"}

            # Sincronizar últimos X dias
            result = self._sync_trades_since(timedelta(days=self.lookback_days))

            # Atualizar estatísticas
            self.sync_stats['total_syncs'] += 1
            self.sync_stats['total_new_trades'] += result.get('saved_trades', 0)
            self.last_sync = datetime.now()

            return result

        except Exception as e:
            self.logger.error(f"Erro na sincronização manual: {e}")
            self.sync_stats['last_error'] = str(e)
            return {"error": str(e)}

    def get_status(self) -> Dict:
        """Retorna status atual do serviço"""
        return {
            'is_running': self.is_running,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'next_sync_in_seconds': self._get_next_sync_seconds(),
            'sync_stats': self.sync_stats,
            'config': {
                'sync_interval': self.sync_interval,
                'lookback_days': self.lookback_days
            },
            'mt5_connected': self._check_mt5_connection()
        }

    def get_trade_summary(self, days: int = 30) -> Dict:
        """Retorna resumo dos trades sincronizados"""
        try:
            # Verificar cache primeiro
            if hasattr(self, '_trade_cache') and hasattr(self, '_cache_time'):
                cache_age = (datetime.now() - self._cache_time).total_seconds()
                if cache_age < 300:  # Cache de 5 minutos
                    return self._trade_cache

            # Buscar do banco
            trades = mlp_storage.get_mt5_trade_history(days=days)
            stats = mlp_storage.get_mt5_trade_statistics(days=days)

            summary = {
                'total_trades': len(trades),
                'period_days': days,
                'win_rate': stats.get('win_rate', 0),
                'total_profit': stats.get('total_profit', 0),
                'best_trade': stats.get('largest_win', 0),
                'worst_trade': stats.get('largest_loss', 0) * -1 if stats.get('largest_loss') else 0,
                'last_updated': max([t['created_at'] for t in trades] + [None]) if trades else None,
                'manual_trades': len([t for t in trades if t.get('magic') == 0]),  # Trades manuais (magic=0)
                'bot_trades': len([t for t in trades if t.get('magic') != 0])    # Trades do bot
            }

            # Cache o resultado
            self._trade_cache = summary
            self._cache_time = datetime.now()

            return summary

        except Exception as e:
            self.logger.error(f"Erro ao obter resumo de trades: {e}")
            return {"error": str(e)}

    # ==========================================
    #       MÉTODOS PRIVADOS
    # ==========================================

    def _sync_loop(self):
        """Loop principal de sincronização"""
        self.logger.info("Loop de sincronização iniciado")
        uptime_start = time.time()

        while not self.stop_flag.is_set():
            try:
                # Executar sincronização
                self.sync_now()

                # Atualizar uptime
                self.sync_stats['uptime_seconds'] = int(time.time() - uptime_start)

                # Aguardar próximo ciclo
                for _ in range(self.sync_interval):
                    if self.stop_flag.is_set():
                        break
                    time.sleep(1)

            except Exception as e:
                self.logger.error(f"Erro no loop de sincronização: {e}")
                self.sync_stats['last_error'] = str(e)
                time.sleep(10)  # Aguardar um pouco em caso de erro

        self.logger.info("Loop de sincronização finalizado")

    def _sync_trades_since(self, since_time: timedelta) -> Dict:
        """Sincroniza trades desde determinado ponto no tempo"""
        try:
            from_date = datetime.now() - since_time
            to_date = datetime.now()

            self.logger.debug(f"Sincronizando trades de {from_date.date()} até {to_date.date()}")

            # Buscar trades do MT5
            deals_mt5 = mt5.history_deals_get(from_date, to_date)

            if deals_mt5 is None:
                return {
                    'status': 'error',
                    'error': 'MT5 retornou None - possível desconexão ou erro',
                    'saved_trades': 0,
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat()
                }

            if len(deals_mt5) == 0:
                return {
                    'status': 'no_data',
                    'message': 'Nenhum trade encontrado no período',
                    'saved_trades': 0,
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat()
                }

            # Converter para formato do banco
            deals_to_save = []
            existing_tickets = {t['ticket'] for t in mlp_storage.get_mt5_trade_history(days=self.lookback_days)}

            for deal in deals_mt5:
                ticket = str(deal.ticket)

                # Só salvar se ainda não existe
                if ticket not in existing_tickets:
                    deal_dict = {
                        "ticket": ticket,
                        "order": str(deal.order),
                        "symbol": deal.symbol,
                        "type": "BUY" if deal.type == mt5.DEAL_TYPE_BUY else "SELL",
                        "entry": "IN" if deal.entry == mt5.DEAL_ENTRY_IN else (
                            "OUT" if deal.entry == mt5.DEAL_ENTRY_OUT else "REVERSAL"
                        ),
                        "magic": deal.magic,
                        "volume": float(deal.volume),
                        "price": float(deal.price),
                        "commission": float(deal.commission),
                        "swap": float(deal.swap),
                        "profit": float(deal.profit),
                        "fee": float(deal.fee),
                        "comment": deal.comment,
                        "external_id": deal.external_id,
                        "time": deal.time
                    }
                    deals_to_save.append(deal_dict)

            # Salvar novos trades
            saved_count = 0
            if deals_to_save:
                saved_count = mlp_storage.save_mt5_trade_history(deals_to_save)
                self.logger.info(f"Salvos {saved_count} novos trades no banco")

            return {
                'status': 'success',
                'saved_trades': saved_count,
                'mt5_trades_found': len(deals_mt5),
                'new_trades': len(deals_to_save),
                'from_date': from_date.isoformat(),
                'to_date': to_date.isoformat(),
                'sync_duration_seconds': (datetime.now() - from_date).total_seconds()
            }

        except Exception as e:
            self.logger.error(f"Erro na sincronização: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'saved_trades': 0
            }

    def _check_mt5_connection(self) -> bool:
        """Verifica se MT5 está conectado"""
        return mt5_connection.is_connected()

    def _get_next_sync_seconds(self) -> Optional[int]:
        """Calcula segundos até próxima sincronização"""
        if not self.last_sync:
            return 0

        elapsed = (datetime.now() - self.last_sync).total_seconds()
        remaining = max(0, self.sync_interval - elapsed)
        return int(remaining)

    # ==========================================
    #       MÉTODOS DE CONFIGURAÇÃO
    # ==========================================

    def update_config(self, sync_interval: Optional[int] = None,
                     lookback_days: Optional[int] = None) -> bool:
        """Atualiza configuração do serviço"""
        try:
            if sync_interval is not None:
                if sync_interval < 10:  # Mínimo 10 segundos
                    sync_interval = 10
                self.sync_interval = sync_interval

            if lookback_days is not None:
                if lookback_days < 1:  # Mínimo 1 dia
                    lookback_days = 1
                self.lookback_days = lookback_days

            self.logger.info(f"Configuração atualizada: interval={self.sync_interval}s, lookback={self.lookback_days}d")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao atualizar configuração: {e}")
            return False


# Instância global do serviço
mt5_trade_sync = MT5TradeSyncService(auto_start=False)
