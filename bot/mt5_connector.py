"""
Conector MT5 para execução de operações de trading
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .config import get_config


@dataclass
class Position:
    """Representa uma posição de trading"""
    ticket: int
    symbol: str
    type: str  # 'BUY' ou 'SELL'
    volume: float
    open_price: float
    current_price: float
    profit: float
    sl: float
    tp: float
    open_time: datetime


@dataclass
class Order:
    """Representa uma ordem pendente"""
    ticket: int
    symbol: str
    type: str
    volume: float
    price: float
    sl: float
    tp: float
    status: str


class MT5Connector:
    """Classe para conexão e operações com MT5"""

    def __init__(self):
        self.config = get_config()
        self.connected = False
        self.initialized = False
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """Conecta ao MT5"""
        try:
            # Verificar se já conectado
            if self.connected and mt5.terminal_info() is not None:
                return True

            # Inicializar MT5
            if not mt5.initialize(
                path=self.config.mt5.mt5_path,
                login=self.config.mt5.login,
                password=self.config.mt5.password,
                server=self.config.mt5.server
            ):
                self.logger.error(f"Falha ao inicializar MT5: {mt5.last_error()}")
                return False

            # Verificar conexão
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("Não foi possível obter informações da conta")
                return False

            self.connected = True
            self.logger.info(f"Conectado ao MT5 - Conta: {account_info.login}, Saldo: {account_info.balance}")
            return True

        except Exception as e:
            self.logger.error(f"Erro na conexão MT5: {str(e)}")
            return False

    def disconnect(self):
        """Desconecta do MT5"""
        try:
            mt5.shutdown()
            self.connected = False
            self.initialized = False
            self.logger.info("Desconectado do MT5")
        except Exception as e:
            self.logger.error(f"Erro ao desconectar: {str(e)}")

    def is_connected(self) -> bool:
        """Verifica se está conectado"""
        return self.connected and mt5.terminal_info() is not None

    def get_symbol_info(self, symbol: str = None) -> Optional[Dict]:
        """Obtém informações do símbolo"""
        symbol = symbol or self.config.trading.symbol

        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.error(f"Símbolo {symbol} não encontrado")
                return None

            return {
                'symbol': symbol_info.name,
                'digits': symbol_info.digits,
                'point': symbol_info.point,
                'spread': symbol_info.spread,
                'bid': symbol_info.bid,
                'ask': symbol_info.ask,
                'volume_min': symbol_info.volume_min,
                'volume_max': symbol_info.volume_max,
                'volume_step': symbol_info.volume_step,
                'trade_contract_size': symbol_info.trade_contract_size
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter informações do símbolo: {str(e)}")
            return None

    def get_market_data(self, symbol: str = None, timeframe: str = 'M1', count: int = 100) -> pd.DataFrame:
        """Obtém dados de mercado"""
        symbol = symbol or self.config.trading.symbol

        try:
            # Converter timeframe para MT5
            tf_dict = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }

            timeframe_mt5 = tf_dict.get(timeframe, mt5.TIMEFRAME_M1)

            # Obter dados
            rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, count)

            if rates is None or len(rates) == 0:
                self.logger.error(f"Não foi possível obter dados para {symbol}")
                return pd.DataFrame()

            # Converter para DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]

            return df

        except Exception as e:
            self.logger.error(f"Erro ao obter dados de mercado: {str(e)}")
            return pd.DataFrame()

    def get_positions(self, symbol: str = None) -> List[Position]:
        """Obtém posições abertas"""
        try:
            positions = mt5.positions_get(symbol=symbol or self.config.trading.symbol)

            if positions is None:
                return []

            position_list = []
            for pos in positions:
                if pos.magic == self.config.trading.magic_number:
                    position = Position(
                        ticket=pos.ticket,
                        symbol=pos.symbol,
                        type='BUY' if pos.type == mt5.POSITION_TYPE_BUY else 'SELL',
                        volume=pos.volume,
                        open_price=pos.price_open,
                        current_price=pos.price_current,
                        profit=pos.profit,
                        sl=pos.sl,
                        tp=pos.tp,
                        open_time=datetime.fromtimestamp(pos.time)
                    )
                    position_list.append(position)

            return position_list

        except Exception as e:
            self.logger.error(f"Erro ao obter posições: {str(e)}")
            return []

    def get_orders(self, symbol: str = None) -> List[Order]:
        """Obtém ordens pendentes"""
        try:
            orders = mt5.orders_get(symbol=symbol or self.config.trading.symbol)

            if orders is None:
                return []

            order_list = []
            for order in orders:
                if order.magic == self.config.trading.magic_number:
                    order_type = self._get_order_type_string(order.type)
                    order = Order(
                        ticket=order.ticket,
                        symbol=order.symbol,
                        type=order_type,
                        volume=order.volume_current,
                        price=order.price_open,
                        sl=order.sl,
                        tp=order.tp,
                        status=self._get_order_status_string(order.state)
                    )
                    order_list.append(order)

            return order_list

        except Exception as e:
            self.logger.error(f"Erro ao obter ordens: {str(e)}")
            return []

    def send_market_order(self, symbol: str, order_type: str, volume: float,
                         sl: float = 0, tp: float = 0) -> Optional[int]:
        """Envia ordem a mercado"""
        try:
            if not self.is_connected():
                self.logger.error("Não conectado ao MT5")
                return None

            # Verificar símbolo
            symbol_info = self.get_symbol_info(symbol)
            if symbol_info is None:
                return None

            # Determinar tipo de ordem MT5
            mt5_order_type = mt5.ORDER_TYPE_BUY if order_type.upper() == 'BUY' else mt5.ORDER_TYPE_SELL

            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_order_type,
                "magic": self.config.trading.magic_number,
                "comment": "MLP Bot Order"
            }

            # Adicionar SL e TP se especificados
            if sl > 0:
                request["sl"] = sl
            if tp > 0:
                request["tp"] = tp

            # Enviar ordem
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Erro ao enviar ordem: {result.retcode} - {result.comment}")
                return None

            self.logger.info(f"Ordem enviada com sucesso. Ticket: {result.order}")
            return result.order

        except Exception as e:
            self.logger.error(f"Erro ao enviar ordem a mercado: {str(e)}")
            return None

    def modify_position(self, ticket: int, sl: float, tp: float) -> bool:
        """Modifica Stop Loss e Take Profit de uma posição"""
        try:
            # Obter posição atual
            positions = mt5.positions_get(ticket=ticket)
            if positions is None or len(positions) == 0:
                self.logger.error(f"Posição {ticket} não encontrada")
                return False

            position = positions[0]

            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": sl,
                "tp": tp
            }

            # Enviar modificação
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Erro ao modificar posição: {result.retcode} - {result.comment}")
                return False

            self.logger.info(f"Posição {ticket} modificada com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao modificar posição: {str(e)}")
            return False

    def close_position(self, ticket: int, volume: float = None) -> bool:
        """Fecha uma posição"""
        try:
            # Obter posição atual
            positions = mt5.positions_get(ticket=ticket)
            if positions is None or len(positions) == 0:
                self.logger.error(f"Posição {ticket} não encontrada")
                return False

            position = positions[0]

            # Determinar tipo de fechamento
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY

            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position.symbol,
                "volume": volume or position.volume,
                "type": close_type,
                "magic": self.config.trading.magic_number,
                "comment": "MLP Bot Close"
            }

            # Enviar ordem de fechamento
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Erro ao fechar posição: {result.retcode} - {result.comment}")
                return False

            self.logger.info(f"Posição {ticket} fechada com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao fechar posição: {str(e)}")
            return False

    def calculate_sl_tp(self, symbol: str, order_type: str, price: float) -> Tuple[float, float]:
        """Calcula Stop Loss e Take Profit baseado na configuração"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if symbol_info is None:
                return 0, 0

            point = symbol_info['point']
            sl_pips = self.config.trading.stop_loss_pips
            tp_pips = self.config.trading.take_profit_pips

            if order_type.upper() == 'BUY':
                sl = price - (sl_pips * point * 10)  # Convert pips to price
                tp = price + (tp_pips * point * 10)
            else:  # SELL
                sl = price + (sl_pips * point * 10)
                tp = price - (tp_pips * point * 10)

            return round(sl, symbol_info['digits']), round(tp, symbol_info['digits'])

        except Exception as e:
            self.logger.error(f"Erro ao calcular SL/TP: {str(e)}")
            return 0, 0

    def _get_order_type_string(self, order_type: int) -> str:
        """Converte tipo de ordem MT5 para string"""
        types = {
            mt5.ORDER_TYPE_BUY: "BUY",
            mt5.ORDER_TYPE_SELL: "SELL",
            mt5.ORDER_TYPE_BUY_LIMIT: "BUY_LIMIT",
            mt5.ORDER_TYPE_SELL_LIMIT: "SELL_LIMIT",
            mt5.ORDER_TYPE_BUY_STOP: "BUY_STOP",
            mt5.ORDER_TYPE_SELL_STOP: "SELL_STOP"
        }
        return types.get(order_type, "UNKNOWN")

    def _get_order_status_string(self, status: int) -> str:
        """Converte status de ordem MT5 para string"""
        statuses = {
            mt5.ORDER_STATE_STARTED: "STARTED",
            mt5.ORDER_STATE_PLACED: "PLACED",
            mt5.ORDER_STATE_CANCELED: "CANCELED",
            mt5.ORDER_STATE_PARTIAL: "PARTIAL",
            mt5.ORDER_STATE_FILLED: "FILLED",
            mt5.ORDER_STATE_REJECTED: "REJECTED",
            mt5.ORDER_STATE_EXPIRED: "EXPIRED"
        }
        return statuses.get(status, "UNKNOWN")

    def get_account_info(self) -> Optional[Dict]:
        """Obtém informações da conta"""
        try:
            account = mt5.account_info()
            if account is None:
                return None

            return {
                'balance': account.balance,
                'equity': account.equity,
                'profit': account.profit,
                'margin': account.margin,
                'margin_free': account.margin_free,
                'margin_level': account.margin_level
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter informações da conta: {str(e)}")
            return None
