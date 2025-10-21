#!/usr/bin/env python3
"""
ESTRATÉGIA DE SCALPING CONSERVADOR PARA GBPUSDc
Executa operações de $1 lucro / $0 perda automaticamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import logging
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd

# Importações locais
try:
    from core.mt5_connection import MT5Connection
except ImportError as e:
    print("Erro ao importar módulos: {}".format(e))
    sys.exit(1)

class ConservativeScalpStrategy:
    """Estratégia de scalping ultra-conservador para GBPUSDc"""

    def __init__(self):
        # Configurações da estratégia GBP
        self.symbol = "GBPUSDc"
        self.timeframe = mt5.TIMEFRAME_M5

        # Parâmetros de risco GBP
        self.max_daily_loss = 25.0
        self.operation_target = 1.0
        self.lot_min = 0.05   # Forex maior volume
        self.lot_max = 0.20
        self.lot_current = self.lot_min

        # Pip value GBP = 0.00001 (Forex muito menor)
        self.pip_value = 0.00001

        # Parâmetros técnicos GBP - Forex mais rápido
        self.sl_points = 80   # GBPUSD mais volátil nas sessões
        self.tp_points = 16   # TP proporcional ao SL
        self.bb_period = 22   # Forex precisa de período maior (mercado rápido)
        self.rsi_period = 16  # RSI período maior para Forex
        self.rsi_neutral_low = 45
        self.rsi_neutral_high = 55
        self.bb_range_min = 300   # GBP range maior devido à volatilidade
        self.bb_range_max = 1500
        self.ema_fast = 21
        self.ema_slow = 50
        self.bb_deviations = 2

        # Status GBP
        self.is_running = False
        self.account_balance = 0.0
        self.account_margin = 0.0

        self.max_consecutive_losses = 3

        # Controle operacional
        self.positions_open = []
        self.daily_pnl = 0.0
        self.consecutive_wins = 0
        self.consecutive_losses = 0

        # Horários Forex
        self.allowed_hours = [
            (8, 0, 11, 30),   # London
            (13, 30, 16, 0),  # NYC
            (17, 0, 19, 0),   # Asya early
        ]

        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - CONSERVATIVE_SCALP_GBP - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/conservative_scalp_gbp_{}.log'.format(datetime.now().strftime("%Y%m%d_%H%M%S"))),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        self.mt5 = MT5Connection()
        self.check_mt5_connection()

    def check_mt5_connection(self):
        """Verifica conexão MT5"""
        try:
            self.mt5.initialize()
        except Exception as e:
            self.logger.error("Falha MT5: {}".format(e))
            sys.exit(1)

        account = mt5.account_info()
        if account is None:
            self.logger.error("Conta GBP não encontrada")
            sys.exit(1)

        self.account_balance = account.balance
        self.account_margin = account.margin_free

        self.logger.info("MT5 OK - Conta: {}".format(account.login))
        self.logger.info("Saldo: ${:.2f}".format(self.account_balance))
        self.logger.info("GBP Strategy Started")

        return True

    def get_market_data(self, bars=100):
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, bars)
        if rates is None:
            self.logger.warning("Sem dados GBP")
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def calculate_indicators(self, df):
        # Bollinger Bands
        df['SMA'] = df['close'].rolling(window=self.bb_period).mean()
        df['STD'] = df['close'].rolling(window=self.bb_period).std()
        df['BB_upper'] = df['SMA'] + (2 * df['STD'])
        df['BB_lower'] = df['SMA'] - (2 * df['STD'])
        df['BB_position'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=16).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=16).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Volume
        df['volume_avg'] = df['tick_volume'].rolling(window=10).mean()
        df['volume_ratio'] = df['tick_volume'] / df['volume_avg']

        return df

    def check_trading_hours(self):
        """Verifica horário GMT"""
        now = datetime.now()
        gmt_hour = now.hour + 3
        if gmt_hour >= 24:
            gmt_hour -= 24

        for start_hour, start_min, end_hour, end_min in self.allowed_hours:
            start_time = start_hour * 60 + start_min
            end_time = end_hour * 60 + end_min
            current_time = gmt_hour * 60 + now.minute

            if start_time <= current_time <= end_time:
                return True
        return False

    def check_range_conditions(self, df):
        last = df.iloc[-1]
        bb_range = last['BB_upper'] - last['BB_lower']

        if not (self.bb_range_min <= bb_range <= self.bb_range_max):
            return False, "Range GBP invalido"

        if not (self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high):
            return False, "RSI GBP: {:.1f}".format(last['RSI'])

        if last['volume_ratio'] < 0.8:
            return False, "Volume GBP baixo"

        prev_close = df.iloc[-2]['close']
        gap = abs(last['open'] - prev_close)
        if gap > 20:
            return False, "Gap GBP alto"

        return True, "GBP ideal"

    def find_entry_signal(self, df):
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # BUY: ≤ 0.25
        if last['BB_position'] <= 0.25:
            if (prev['close'] < prev['open'] and
                last['close'] > last['open'] and
                last['low'] <= last['BB_lower'] + 1):
                return "BUY", last['close'] + 0.01  # 0.01 para Forex

        # SELL: ≥ 0.8
        elif last['BB_position'] >= 0.8:
            if (prev['close'] > prev['open'] and
                last['close'] < last['open'] and
                last['high'] >= last['BB_upper'] - 1):
                return "SELL", last['close'] - 0.01

        return None, None

    def calculate_lot_size(self):
        pip_value = 0.00001  # Forex
        risk_per_trade = 5.0

        if self.consecutive_losses >= 2:
            self.lot_current = max(self.lot_min, self.lot_current * 0.5)
        elif self.consecutive_wins >= 3:
            self.lot_current = min(self.lot_max, self.lot_current * 1.2)

        calculated_lot = risk_per_trade / (self.sl_points * pip_value)
        final_lot = max(self.lot_min, min(calculated_lot, self.lot_max))

        self.logger.info("GBP Lot: {:.2f}".format(final_lot))
        return round(final_lot, 2)

    def execute_trade(self, direction, entry_price):
        try:
            pip_value = 0.00001  # Forex
            if direction == "BUY":
                sl_price = entry_price - (self.sl_points * pip_value)
                tp_price = entry_price + (self.tp_points * pip_value)
            else:
                sl_price = entry_price + (self.sl_points * pip_value)
                tp_price = entry_price - (self.tp_points * pip_value)

            lot_size = self.calculate_lot_size()

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
                "volume": lot_size,
                "price": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "comment": "GBP_SCALP_{}".format(direction),
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.positions_open.append({
                    'ticket': result.order,
                    'direction': direction,
                    'timestamp': datetime.now()
                })
                self.logger.info("GBP TRADE: {} executado".format(direction))
                return True
            else:
                self.logger.error("falha GBP trade")
                return False

        except Exception as e:
            self.logger.error("erro GBP: {}".format(e))
            return False

    def check_positions(self):
        if not self.positions_open:
            return

        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return

        active_tickets = {pos.ticket for pos in positions if pos.symbol == self.symbol}

        for pos in self.positions_open[:]:
            if pos['ticket'] not in active_tickets:
                deals = mt5.history_deals_get(ticket=pos['ticket'])
                if deals:
                    pnl = sum(deal.profit for deal in deals if deal.ticket == pos['ticket'])
                    self.daily_pnl += pnl

                    if pnl > 0:
                        self.consecutive_wins += 1
                        self.consecutive_losses = 0
                        self.logger.info("WIN GBP ${:.2f}".format(pnl))
                    else:
                        self.consecutive_losses += 1
                        self.consecutive_wins = 0
                        self.logger.warning("LOSS GBP ${:.2f}".format(pnl))

                self.positions_open.remove(pos)

        if abs(self.daily_pnl) >= self.max_daily_loss:
            self.logger.error("GBP Limite diario excedido")
            self.stop()

    def main_loop(self):
        self.logger.info("GBP Strategy Started")
        self.logger.info("GBP: $1 target, Forex hours")

        self.is_running = True

        while self.is_running:
            try:
                if not self.check_trading_hours():
                    time.sleep(300)
                    continue

                df = self.get_market_data(50)
                if df is None or len(df) < 50:
                    self.logger.warning("GBP: no data")
                    time.sleep(10)
                    continue

                df = self.calculate_indicators(df)

                market_ok, msg = self.check_range_conditions(df)
                if not market_ok:
                    self.logger.info("GBP waiting: {}".format(msg))
                    time.sleep(10)
                    continue

                signal, price = self.find_entry_signal(df)
                if signal is None:
                    self.logger.info("GBP waiting for perfect setup...")
                    time.sleep(10)
                    continue

                self.logger.info("GBP PERFECT SETUP: {} @ {:.5f}".format(signal, price))

                if self.execute_trade(signal, price):
                    self.logger.info("GBP trade executed!")
                else:
                    self.logger.error("GBP failed")

                time.sleep(60)
                self.check_positions()

                if self.consecutive_losses >= 3:
                    self.logger.warning("3 losses GBP - pause")
                    time.sleep(3600)

            except KeyboardInterrupt:
                self.logger.info("GBP stopped by user")
                self.stop()
                break
            except Exception as e:
                self.logger.error("GBP error: {}".format(e))
                time.sleep(30)

    def stop(self):
        self.logger.info("Stopping GBP strategy")
        self.is_running = False
        self.logger.info("GBP P&L: ${:.2f}".format(self.daily_pnl))

def main():
    strategy = ConservativeScalpStrategy()
    try:
        strategy.main_loop()
    except KeyboardInterrupt:
        strategy.stop()
    except Exception as e:
        print("GBP critical error: {}".format(e))
        strategy.stop()

if __name__ == "__main__":
    main()
