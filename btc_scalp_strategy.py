#!/usr/bin/env python3
"""
ESTRATÉGIA DE SCALPING CONSERVADOR PARA BTCCURDC
Executa operações de $1 lucro / $0 perda automaticamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import logging
import signal
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# Importações locais
try:
    from core.mt5_connection import MT5Connection
    from models import requests
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)

# Configuração do logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CONSERVATIVE_SCALP - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/conservative_scalp_btc_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConservativeScalpStrategy:
    """Estratégia de scalping ultra-conservador para BTCUSDc"""

    def __init__(self):
        # Configurações da estratégia
        self.symbol = "BTCUSDc"
        self.timeframe = mt5.TIMEFRAME_M5  # 5 minutos

        # Parâmetros de risco
        self.max_daily_loss = 50.0  # Máximo $50 perda por dia
        self.operation_target = 1.0  # Meta $1 por operação
        self.lot_min = 0.01
        self.lot_max = 0.05
        self.lot_current = self.lot_min

        # Parâmetros técnicos
        self.sl_points = 80  # Stop Loss: 80 pontos
        self.tp_points = 16  # Take Profit: 16 pontos
        self.ema_fast = 21
        self.ema_slow = 50
        self.bb_period = 20
        self.bb_deviations = 2
        self.rsi_period = 14
        self.rsi_neutral_low = 45
        self.rsi_neutral_high = 55
        self.bb_range_min = 100  # Adicionado
        self.bb_range_max = 1500  # Adicionado

        # Controle operacional
        self.positions_open = []
        self.daily_pnl = 0.0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3

        # Status da estratégia
        self.is_running = False
        self.account_balance = 0.0
        self.account_margin = 0.0

        # Horários de operação (GMT) convertidos para cobertura brasileira
        self.allowed_hours = [
            (8, 0, 11, 30),   # London open (9:00-12:30 BRT)
            (13, 30, 16, 0), # New York session (14:30-17:00 BRT)
            (17, 0, 21, 0),  # Extended: Asya session overlap (18:00-22:00 BRT)
        ]

        # Conexão MT5
        self.mt5 = MT5Connection()
        self.check_mt5_connection()

    def check_mt5_connection(self):
        """Verifica conexão MT5"""
        try:
            self.mt5.initialize()
        except Exception as e:
            logger.error("Falha na inicialização MT5: {}".format(e))
            sys.exit(1)

        account = mt5.account_info()
        if account is None:
            logger.error("Falha ao obter informações da conta")
            sys.exit(1)

        self.account_balance = account.balance
        self.account_margin = account.margin_free

        logger.info("MT5 conectado - Conta: {}".format(account.login))
        logger.info("Saldo: ${:.2f}".format(self.account_balance))
        logger.info("Margem livre: ${:.2f}".format(self.account_margin))
        logger.info("Estrategia Conservadora Iniciada: {}".format(self.symbol))

        return True

    def get_market_data(self, bars=100):
        """Obtém dados de mercado"""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, bars)
        if rates is None:
            logger.warning("Sem dados para {}".format(self.symbol))
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def calculate_indicators(self, df):
        """Calcula indicadores técnicos"""
        # EMA
        df['EMA_fast'] = df['close'].ewm(span=self.ema_fast).mean()
        df['EMA_slow'] = df['close'].ewm(span=self.ema_slow).mean()

        # Bollinger Bands
        df['SMA'] = df['close'].rolling(window=self.bb_period).mean()
        df['STD'] = df['close'].rolling(window=self.bb_period).std()
        df['BB_upper'] = df['SMA'] + (self.bb_deviations * df['STD'])
        df['BB_lower'] = df['SMA'] - (self.bb_deviations * df['STD'])
        df['BB_position'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # Volume Analysis
        df['volume_avg'] = df['tick_volume'].rolling(window=10).mean()
        df['volume_ratio'] = df['tick_volume'] / df['volume_avg']

        return df

    def check_trading_hours(self):
        """Verifica se está em horário permitido (GMT)"""
        # Converte BRT para GMT (BRT = GMT-3, então GMT = BRT+3)
        now = datetime.now()
        gmt_hour = now.hour + 3  # UTC-3 para GMT

        # Ajusta para 24h se passar de 24
        if gmt_hour >= 24:
            gmt_hour -= 24

        current_hour = gmt_hour
        current_minute = now.minute

        for start_hour, start_min, end_hour, end_min in self.allowed_hours:
            start_time = start_hour * 60 + start_min
            end_time = end_hour * 60 + end_min
            current_time = current_hour * 60 + current_minute

            if start_time <= current_time <= end_time:
                return True

        return False

    def calculate_market_ideal_score(self, df):
        """Calcula percentual quão próximo estamos das condições ideais para entrada"""
        last = df.iloc[-1]
        prev_close = df.iloc[-2]['close']

        # Calcula cada score individual (0-1) e média
        scores = {}
        total_score = 0

        # 1. Range BB
        bb_range = last['BB_upper'] - last['BB_lower']
        if self.bb_range_min <= bb_range <= self.bb_range_max:
            ideal_range = (self.bb_range_min + self.bb_range_max) / 2
            range_diff = abs(bb_range - ideal_range) / (self.bb_range_max - self.bb_range_min) * 2
            scores['range'] = max(0, 1 - range_diff)
            total_score += 1
        else:
            scores['range'] = 0

        # 2. RSI
        rsi_distance = abs(last['RSI'] - 50) / 10
        scores['rsi'] = max(0, 1 - rsi_distance)
        if self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high:
            total_score += 1

        # 3. Volume
        scores['volume'] = min(last['volume_ratio'], 2.0) / 2.0
        if last['volume_ratio'] >= 0.8:
            total_score += 1

        # 4. Gap
        gap = abs(last['open'] - prev_close)
        gap_score = max(0, 1 - (gap / 20.0))
        scores['gap'] = gap_score
        if gap <= 20:
            total_score += 1

        # 5. Bollinger Position - MUITO AGRESSIVO
        if last['BB_position'] <= 0.1:  # Threshold ultra-agressivo: 10%
            bb_pos_score = max(0, (0.1 - last['BB_position']) * 10.0)
        elif last['BB_position'] >= 0.8:
            bb_pos_score = max(0, (last['BB_position'] - 0.8) * 3.33)
        else:
            bb_pos_score = 0

        scores['bb_position'] = bb_pos_score
        total_score += max(0, min(1, bb_pos_score))

        # Score final
        conditions_pass = (self.bb_range_min <= bb_range <= self.bb_range_max and
                          self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high and
                          last['volume_ratio'] >= 0.8 and
                          gap <= 20)

        if conditions_pass:
            final_score = (total_score / 6) * 100
        else:
            final_score = max(0, (total_score / 6) * 60)

        return round(final_score)

    def check_range_conditions(self, df):
        """Verifica condições de range para scalping"""
        last = df.iloc[-1]

        bb_range = last['BB_upper'] - last['BB_lower']
        if not (self.bb_range_min <= bb_range <= self.bb_range_max):
            return False, "Range fora dos parâmetros ideais"

        if not (self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high):
            return False, "RSI não neutro: {:.1f}".format(last['RSI'])

        if last['volume_ratio'] < 0.8:
            return False, "Volume baixo: {:.2f}".format(last['volume_ratio'])

        prev_close = df.iloc[-2]['close']
        gap = abs(last['open'] - prev_close)
        if gap > 20:
            return False, "Gap muito alto: {:.1f} pontos".format(gap)

        return True, "Condições ideais para range"

    def find_entry_signal(self, df):
        """Busca sinais de entrada"""
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Setup BUY - ULTRA AGRESSIVO
        if last['BB_position'] <= 0.1:  # Threshold ultra-reduzido para 10%
            if (prev['close'] < prev['open'] and
                last['close'] > last['open'] and
                last['low'] <= last['BB_lower'] + 1):
                return "BUY", last['close'] + 0.1

        # Setup SELL
        elif last['BB_position'] >= 0.8:
            if (prev['close'] > prev['open'] and
                last['close'] < last['open'] and
                last['high'] >= last['BB_upper'] - 1):
                return "SELL", last['close'] - 0.1

        return None, None

    def calculate_lot_size(self):
        """Calcula tamanho do lote baseado em risco"""
        risk_per_trade = 5.0
        pip_value = 0.01  # BTC

        if self.consecutive_losses >= 2:
            self.lot_current = max(self.lot_min, self.lot_current * 0.5)
        elif self.consecutive_wins >= 3:
            self.lot_current = min(self.lot_max, self.lot_current * 1.2)

        calculated_lot = risk_per_trade / (self.sl_points * pip_value)
        final_lot = max(self.lot_min, min(calculated_lot, self.lot_max))

        logger.info("Lot calculado: {:.3f}".format(final_lot))
        return round(final_lot, 2)

    def execute_trade(self, direction, entry_price):
        """Executa trade automaticamente"""
        try:
            pip_value = 0.01  # BTC
            if direction == "BUY":
                sl_price = entry_price - (self.sl_points * pip_value)
                tp_price = entry_price + (self.tp_points * pip_value)
            else:
                sl_price = entry_price + (self.sl_points * pip_value)
                tp_price = entry_price - (self.tp_points * pip_value)

            lot_size = self.calculate_lot_size()

            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                logger.error("Info simbolo {} indisponivel".format(self.symbol))
                return False

            margin_required = symbol_info.margin_initial * lot_size
            if self.account_margin < margin_required * 1.2:
                logger.warning("Margem insuficiente")
                return False

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
                "volume": lot_size,
                "price": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "comment": "BTC_SCALP_{}".format(direction),
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                position = {
                    'ticket': result.order,
                    'direction': direction,
                    'entry_price': entry_price,
                    'sl_price': sl_price,
                    'tp_price': tp_price,
                    'lot_size': lot_size,
                    'timestamp': datetime.now()
                }
                self.positions_open.append(position)

                self.logger.info("TRADE EXECUTADO: {} BTC".format(direction))
                self.logger.info("Ticket: {}".format(result.order))
                return True
            else:
                self.logger.error("Falha execucao: {}".format(result.retcode))
                return False

        except Exception as e:
            self.logger.error("Erro execucao: {}".format(e))
            return False

    def check_positions(self):
        """Verifica posições abertas e atualiza P&L"""
        if not self.positions_open:
            return

        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return

        active_tickets = {pos.ticket for pos in positions if pos.symbol == self.symbol}

        for i in range(len(self.positions_open) - 1, -1, -1):
            pos = self.positions_open[i]
            if pos['ticket'] not in active_tickets:
                deals = mt5.history_deals_get(ticket=pos['ticket'])
                if deals:
                    pnl = sum(deal.profit for deal in deals if deal.ticket == pos['ticket'])
                    self.daily_pnl += pnl

                    if pnl > 0:
                        self.consecutive_wins += 1
                        self.consecutive_losses = 0
                        self.logger.info("WIN ${:.2f}".format(pnl))
                    else:
                        self.consecutive_losses += 1
                        self.consecutive_wins = 0
                        self.logger.warning("LOSS ${:.2f}".format(pnl))

                self.positions_open.pop(i)

        if abs(self.daily_pnl) >= self.max_daily_loss:
            self.logger.error("Limite diario excedido")
            self.stop()

    def main_loop(self):
        """Loop principal da estratégia"""
        logger.info("ESTRATEGIA BTC INICIADA - {}".format(self.symbol))
        logger.info("Objetivo: $1 lucro por operacao")
        logger.info("Analisando a cada 10 segundos...")

        self.is_running = True

        while self.is_running:
            try:
                if not self.check_trading_hours():
                    time.sleep(300)
                    continue

                df = self.get_market_data(50)
                if df is None or len(df) < 50:
                    logger.warning("Sem dados suficientes")
                    time.sleep(10)
                    continue

                df = self.calculate_indicators(df)
                logger.info("==".format(self.symbol))
                self.analyze_current_market(df)

                range_ok, range_msg = self.check_range_conditions(df)
                if not range_ok:
                    logger.info("Aguardando: {}".format(range_msg))
                    time.sleep(10)
                    continue

                signal, entry_price = self.find_entry_signal(df)
                if signal is None:
                    self.logger.info("Aguardando sinal perfeito...")
                    time.sleep(10)
                    continue

                self.logger.info("SETUP PERFEITO: {} @ {:.2f}".format(signal, entry_price))

                if self.execute_trade(signal, entry_price):
                    self.logger.info("Trade executado!")
                else:
                    self.logger.error("Falhou execucao")

                time.sleep(60)
                self.check_positions()

                if self.consecutive_losses >= self.max_consecutive_losses:
                    self.logger.warning("3 perdas consecutivas")
                    time.sleep(3600)

            except KeyboardInterrupt:
                self.logger.info("Interrompido pelo usuario")
                self.stop()
                break
            except Exception as e:
                self.logger.error("Erro no loop: {}".format(e))
                time.sleep(30)

    def analyze_current_market(self, df):
        """Analisa e exibe condições atuais do mercado"""
        last = df.iloc[-1]

        logger.info("=" * 50)
        logger.info("ANALISE DE MERCADO ATUAL - {}".format(self.symbol.upper()))
        logger.info("=" * 50)

        # Parâmetros da estratégia
        logger.info("[PARAMETROS DA ESTRATEGIA]")
        logger.info("Stop Loss: {} pontos".format(self.sl_points))
        logger.info("Take Profit: {} pontos".format(self.tp_points))
        logger.info("Range BB Target: {}-{} pontos".format(self.bb_range_min, self.bb_range_max))
        logger.info("RSI Target: {}-{}".format(self.rsi_neutral_low, self.rsi_neutral_high))
        logger.info("Objetivo: ${:.2f} lucro por operacao".format(self.operation_target))
        logger.info("Perda Max: ${:.0f}".format(self.max_daily_loss))

        # Dados do preço atual
        logger.info("[DADOS DE PRECO ATUAL]")
        logger.info("Preco Atual: {:.5f}".format(last['close']))
        logger.info("Preco Maximo: {:.5f}".format(last['high']))
        logger.info("Preco Minimo: {:.5f}".format(last['low']))
        logger.info("Volume: {}".format(int(last['tick_volume'])))

        # Indicadores calculados
        logger.info("[INDICADORES TECNICOS]")
        try:
            logger.info("Bollinger Superior: {:.2f}".format(last['BB_upper']))
            logger.info("Bollinger Inferior: {:.2f}".format(last['BB_lower']))
            bb_range = last['BB_upper'] - last['BB_lower']
            logger.info("Range BB Atual: {:.2f} pontos".format(bb_range))
            logger.info("Posicao no Range: {:.2f}%".format(last['BB_position'] * 100))
            logger.info("RSI Atual: {:.1f}".format(last['RSI']))

            # Volume analysis
            logger.info("[ANALISE DE VOLUME]")
            logger.info("Volume Medio: {:.1f}".format(last['volume_avg']))
            logger.info("Ratio Volume: {:.2f}".format(last['volume_ratio']))

            # Verificações de condição
            logger.info("[VERIFICACAO DE CONDICOES]")

            range_ok = self.bb_range_min <= bb_range <= self.bb_range_max
            logger.info("OK Range BB ({}-{}): {:.2f} -> {}".format(self.bb_range_min, self.bb_range_max, bb_range, "PASSOU" if range_ok else "REJEITOU"))

            rsi_ok = self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high
            logger.info("OK RSI ({}-{}): {:.1f} -> {}".format(self.rsi_neutral_low, self.rsi_neutral_high, last['RSI'], "PASSOU" if rsi_ok else "REJEITOU"))

            volume_ok = last['volume_ratio'] >= 0.8
            logger.info("OK Volume (>=0.8): {:.2f} -> {}".format(last['volume_ratio'], "PASSOU" if volume_ok else "REJEITOU"))

            prev_close = df.iloc[-2]['close']
            gap = abs(last['open'] - prev_close)
            gap_ok = gap <= 20
            logger.info("OK Gap (<=20pts): {:.1f}pt -> {}".format(gap, "PASSOU" if gap_ok else "REJEITOU"))

            # Overall assessment
            all_ok = range_ok and rsi_ok and volume_ok and gap_ok
            status_msg = "CONDICOES IDEAIS PARA TRADE" if all_ok else "AGUARDANDO MELHORAS"
            logger.info("STATUS GERAL: {}".format(status_msg))

        except Exception as e:
            logger.error("Erro no calculo dos indicadores: {}".format(e))
            logger.info("ERRO TEKCO - VERIFICAR INDICADORES")

        logger.info("=" * 50)

        return last

    def stop(self):
        """Para estratégia"""
        self.logger.info("PARANDO ESTRATEGIA BTC")
        self.is_running = False

        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            for pos in positions:
                if pos.symbol == self.symbol:
                    self.logger.info("Fechando posicao: {}".format(pos.ticket))
                    try:
                        mt5.order_send({
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": self.symbol,
                            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                            "position": pos.ticket,
                            "volume": pos.volume,
                            "price": mt5.symbol_info_tick(self.symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(self.symbol).ask,
                        })
                    except Exception as e:
                        self.logger.error("Erro fechamento: {}".format(e))

        self.logger.info("P&L Final: ${:.2f}".format(self.daily_pnl))
        mt5.shutdown()

def main():
    """Ponto de entrada principal"""
    strategy = ConservativeScalpStrategy()

    try:
        strategy.main_loop()

    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario")
        strategy.stop()
    except Exception as e:
        print(f"Erro critico: {e}")
        strategy.stop()

if __name__ == "__main__":
    main()
