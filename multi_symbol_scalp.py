#!/usr/bin/env python3
"""
ESTRATÉGIA DE SCALPING CONSERVADOR MULTI-SÍMBOLOS
Executa operações em BTCUSDc, XAUUSDc e GBPUSDc simultaneamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import logging
import threading
import signal
import sys
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# Importações locais
try:
    from core.mt5_connection import MT5Connection
    from conservative_scalp_strategy import ConservativeScalpStrategy
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)

# Variável global para controle de parada de todas as threads
shutdown_event = threading.Event()

def create_logger_for_symbol(symbol):
    """Cria logger específico para cada símbolo"""
    logger = logging.getLogger(f'conservative_scalp_{symbol.lower()}')
    logger.setLevel(logging.INFO)

    # Remove handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Cria handler de arquivo específico
    file_handler = logging.FileHandler(
        f'conservative_scalp_{symbol.lower()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - [{}] - %(levelname)s - %(message)s'.format(symbol.upper())
    ))

    # Cria handler de console específico para esta thread
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - [{}] - %(levelname)s - %(message)s'.format(symbol.upper())
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Impede que logs subam para o logger pai
    logger.propagate = False

    return logger

def run_strategy_for_symbol(symbol, pip_value):
    """Executa estratégia para um símbolo específico"""

    # Cria logger específico para este símbolo
    logger = create_logger_for_symbol(symbol)

    logger.info("="*60)
    logger.info("INICIANDO ESTRATEGIA PARA {}".format(symbol.upper()))
    logger.info("="*60)

    try:
        print("=".format(symbol.upper()))
        print("INICIANDO THREAD {}".format(symbol.upper()))
        print("=".format(symbol.upper()))

        # Instancia estratégia com símbolo específico
        strategy = MultiSymbolConservativeScalpStrategy(symbol, pip_value)

        # Executa a estratégia
        strategy.main_loop()

    except Exception as e:
        logger.error("Erro crítico na estratégia {}: {}".format(symbol, e))

    logger.info("=" * 60)
    logger.info("ESTRATEGIA FINALIZADA PARA {}".format(symbol.upper()))
    logger.info("=" * 60)

def signal_handler(signum, frame):
    """Handler para Ctrl+C - sinaliza parada de todas as threads"""
    print("\n" + "=" * 80)
    print("SIGNAL RECEBIDO - SOLICITANDO PARADA DE TODAS AS ESTRATÉGIAS")
    print("=" * 80)

    # Ativa evento global de parada
    shutdown_event.set()

    print("Shutdown event ativado - threads vão parar...")
    print("=" * 80)

def main():
    """Executa estratégias múltiplas para diferentes símbolos"""

    # Configura signal handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 80)
    print("ESTRATÉGIA DE SCALPING CONSERVADOR MULTI-SÍMBOLOS")
    print("=" * 80)

    # Configuração dos símbolos e seus parâmetros
    symbols_config = {
        'BTCUSDc': {
            'pip_value': 0.01,  # BTC tem pip_value menor
            'name': 'Bitcoin'
        },
        'XAUUSDc': {
            'pip_value': 0.10,  # Ouro com maior quantidade
            'name': 'Gold'
        },
        'GBPUSDc': {
            'pip_value': 0.00001,  # Forex com menor quantidade
            'name': 'GBP/USD'
        }
    }

    # Lista para armazenar as threads
    threads = []

    try:
        print("Iniciando estratégias para os seguintes símbolos:")
        for symbol, config in symbols_config.items():
            print(f"  📊 {symbol} - {config['name']} (Pip: {config['pip_value']})")

        print("\n" + "-" * 80)
        print("Cada estratégia terá seu próprio log e operará independente!")
        print("Monitor cada arquivo conservative_scalp_[symbol]_{timestamp}.log")
        print("-" * 80)

        # Inicia estratégia para cada símbolo em thread separada
        for symbol, config in symbols_config.items():
            thread = threading.Thread(
                target=run_strategy_for_symbol,
                args=(symbol, config['pip_value']),
                name=f"Strategy_{symbol}"
            )
            threads.append(thread)
            thread.start()

            # Pequena pausa entre inicializações
            time.sleep(2)

        print("=" * 80)
        print("TODAS AS ESTRATÉGIAS INICIADAS!")
        print("Pressione CTRL+C para parar todas as estratégias simultaneamente")
        print("=" * 80)

        # Mantém principal thread vivo
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n" + "=" * 80)
        print("INTERRUPÇÃO SOLICITADA - PARANDO TODAS AS ESTRATÉGIAS")
        print("=" * 80)

        # Não consigo matar threads diretamente, mas posso mostrar mensagem
        print("As estratégias serão interrompidas automaticamente pelas threads")
        print("Aguarde a finalização natural de cada uma")
        print("=" * 80)

        # Espera as threads terminarem (timeout de 10 segundos)
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=10)

        print("=" * 80)
        print("TODAS AS ESTRATÉGIAS FINALIZADAS!")
        print("=" * 80)

    except Exception as e:
        print(f"Erro crítico no sistema multi-símbolos: {e}")
        import traceback
        traceback.print_exc()

class MultiSymbolConservativeScalpStrategy:
    """Versão multi-símbolos da estratégia conservadora"""

    def __init__(self, symbol, pip_value):
        # Parâmetros específicos do símbolo
        self.symbol = symbol
        self.pip_value = pip_value
        self.timeframe = mt5.TIMEFRAME_M5  # 5 minutos

        # Parâmetros de risco (ajustados para multi-símbolos)
        self.max_daily_loss = 25.0  # Máximo $25 perda por dia por símbolo
        self.operation_target = 1.0  # Meta $1 por operação

        # Lot sizing baseado no símbolo
        if symbol == 'BTCUSDc':
            self.lot_min = 0.01
            self.lot_max = 0.03  # BTC com mais cautela
            self.sl_points = 80
            self.tp_points = 16
            self.rsi_neutral_low = 40
            self.rsi_neutral_high = 60
        elif symbol == 'XAUUSDc':
            self.lot_min = 0.02
            self.lot_max = 0.08  # Ouro tolera mais volume
            self.sl_points = 60
            self.tp_points = 12  # Ouro mais previsível
            self.rsi_neutral_low = 45
            self.rsi_neutral_high = 55
        elif symbol == 'GBPUSDc':
            self.lot_min = 0.05
            self.lot_max = 0.20  # Forex mais volume
            self.sl_points = 80
            self.tp_points = 16  # Forex intradiário
            self.rsi_neutral_low = 45
            self.rsi_neutral_high = 55
        else:
            self.lot_min = 0.01
            self.lot_max = 0.05

        self.lot_current = self.lot_min

        # Parâmetros técnicos (adaptados conforme sinal)
        self.ema_fast = 21
        self.ema_slow = 50
        if symbol == 'BTCUSDc':
            # BTC mais volátil
            self.bb_period = 20
            self.bb_deviations = 2
            self.rsi_period = 14
            self.bb_range_min = 200
            self.bb_range_max = 1200
        elif symbol == 'XAUUSDc':
            # Ouro mais estável
            self.bb_period = 18
            self.bb_deviations = 2
            self.rsi_period = 12
            self.bb_range_min = 150
            self.bb_range_max = 800
        elif symbol == 'GBPUSDc':
            # Forex rápido
            self.bb_period = 22
            self.bb_deviations = 2
            self.rsi_period = 16
            self.bb_range_min = 300
            self.bb_range_max = 1500
        else:
            self.bb_period = 20
            self.bb_deviations = 2
            self.rsi_period = 14
            self.bb_range_min = 200
            self.bb_range_max = 1200

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

        # Anatomia horária - BTC pode operar mais horas, outros limitado revanche
        if symbol == 'BTCUSDc':
            # BTC 24/7 com 4 sessões principais
            self.allowed_hours = [
                (0, 0, 6, 0),    # Asya-London overlap
                (8, 0, 12, 0),   # London-NYC fingers
                (13, 30, 17, 0), # NYC close
                (17, 0, 23, 59), # Asya-NYC
            ]
        else:
            # Forex/Ouro limitado excellence
            self.allowed_hours = [
                (8, 0, 11, 30),   # London open
                (13, 30, 16, 0), # NYC session
                (17, 0, 19, 0),  # Asya early
            ]

        # Logger específico para este símbolo
        self.logger = create_logger_for_symbol(symbol)

        # Configure mata propagação para logger root
        root_logger = logging.getLogger()
        root_logger.disabled = True  # Disable root logger completely

        # Conexão MT5
        self.mt5 = MT5Connection()
        self.check_mt5_connection()

    def check_mt5_connection(self):
        """Verifica conexão MT5"""
        try:
            self.mt5.initialize()
        except Exception as e:
            self.logger.error("Falha na inicialização MT5: {}".format(e))
            sys.exit(1)

        account = mt5.account_info()
        if account is None:
            self.logger.error("Falha ao obter informações da conta")
            sys.exit(1)

        self.account_balance = account.balance
        self.account_margin = account.margin_free

        self.logger.info("MT5 conectado - Conta: {}".format(account.login))
        self.logger.info("Saldo: ${:.2f}".format(self.account_balance))
        self.logger.info("Margem livre: ${:.2f}".format(self.account_margin))
        self.logger.info("Estrategia Conservadora Iniciada: {}".format(self.symbol))

        return True

    def get_market_data(self, bars=100):
        """Obtém dados de mercado"""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, bars)
        if rates is None:
            self.logger.warning("Sem dados para {}".format(self.symbol))
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
        if self.bb_range_min <= bb_range <= self.bb_range_max:  # Dentro do range aceitável
            # Quanto mais próximo do centro, melhor
            ideal_range = (self.bb_range_min + self.bb_range_max) / 2
            range_diff = abs(bb_range - ideal_range) / (self.bb_range_max - self.bb_range_min) * 2
            scores['range'] = max(0, 1 - range_diff)  # 1 = perfeito, 0 = limite
            total_score += 1  # passa = +1 ponto
        else:
            scores['range'] = 0
            total_score += 0

        # 2. RSI
        rsi_distance = abs(last['RSI'] - 50) / 10  # desvio máximo de 10 pontos
        scores['rsi'] = max(0, 1 - rsi_distance)
        if self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high:
            total_score += 1  # passa = +1 ponto

        # 3. Volume
        scores['volume'] = min(last['volume_ratio'], 2.0) / 2.0  # máximo 200% como 1.0
        if last['volume_ratio'] >= 0.8:
            total_score += 1  # passa = +1 ponto

        # 4. Gap
        gap = abs(last['open'] - prev_close)
        gap_score = max(0, 1 - (gap / 20.0))  # gap máximo 20 pontos = 0
        scores['gap'] = gap_score
        if gap <= 20:
            total_score += 1  # passa = +1 ponto

        # 5. Bollinger Position
        if last['BB_position'] <= 0.3:  # próximo da banda inferior
            bb_pos_score = max(0, (0.3 - last['BB_position']) * 3.33)  # próximo de 0%
        elif last['BB_position'] >= 0.8:  # próximo da banda superior
            bb_pos_score = max(0, (last['BB_position'] - 0.8) * 3.33)  # próximo de 100%
        else:
            bb_pos_score = 0  # zona neutra = ruim para scalping

        scores['bb_position'] = bb_pos_score
        total_score += max(0, min(1, bb_pos_score))  # +0-1 ponto baseado na proximidade

        # Score final
        conditions_pass = (self.bb_range_min <= bb_range <= self.bb_range_max and
                          self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high and
                          last['volume_ratio'] >= 0.8 and
                          gap <= 20)

        if conditions_pass:
            # Todas condições passam: score baseado na qualidade
            final_score = (total_score / 6) * 100  # máximo 100%
        else:
            # Alguma condição falha: score reduzido
            final_score = max(0, (total_score / 6) * 60)  # máximo 60% se faltar condições

        return round(final_score)

    def check_range_conditions(self, df):
        """Verifica condições de range para scalping"""
        last = df.iloc[-1]

        # Range específico por símbolo
        bb_range = last['BB_upper'] - last['BB_lower']
        if not (self.bb_range_min <= bb_range <= self.bb_range_max):
            return False, "Range fora dos parâmetros ideais"

        # RSI
        if not (self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high):
            return False, "RSI não neutro: {:.1f}".format(last['RSI'])

        # Volume
        if last['volume_ratio'] < 0.8:
            return False, "Volume baixo: {:.2f}".format(last['volume_ratio'])

        # Gap
        prev_close = df.iloc[-2]['close']
        gap = abs(last['open'] - prev_close)
        if gap > 20:  # 20 pontos max gap
            return False, "Gap muito alto: {:.1f} pontos".format(gap)

        return True, "Condições ideais para range"

    def find_entry_signal(self, df):
        """Busca sinais de entrada"""
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Setup BUY
        if last['BB_position'] <= 0.3:  # Próximo da banda inferior
            # Confirmação: Alça rosa após candle azul em baixa
            if (prev['close'] < prev['open'] and  # Candle anterior negativo
                last['close'] > last['open'] and   # Candle atual positivo
                last['low'] <= last['BB_lower'] + 1):  # Toca a banda inferior
                return "BUY", last['close'] + 0.1  # Entrada acima da mínima

        # Setup SELL
        elif last['BB_position'] >= 0.8:  # Próximo da banda superior
            # Confirmação: Alça azul após candle vermelho em alta
            if (prev['close'] > prev['open'] and  # Candle anterior positivo
                last['close'] < last['open'] and   # Candle atual negativo
                last['high'] >= last['BB_upper'] - 1):  # Toca a banda superior
                return "SELL", last['close'] - 0.1  # Entrada abaixo da máxima

        return None, None

    def calculate_lot_size(self):
        """Calcula tamanho do lote baseado em risco"""
        # Risk: máximo 0.5% do capital por operação ($5 max por trade)

        # Ajusta lote baseado em performance
        if self.consecutive_losses >= 2:
            self.lot_current = max(self.lot_min, self.lot_current * 0.5)  # Reduz 50%
        elif self.consecutive_wins >= 3:
            self.lot_current = min(self.lot_max, self.lot_current * 1.2)  # Aumenta 20%

        # Calcula baseado no risco
        risk_per_trade = 5.0  # $5 máximo por trade
        # Convert SL points to total risk (multiplica por valor do tick)
        calculated_lot = risk_per_trade / (self.sl_points * self.pip_value)

        # Limita aos ranges
        final_lot = max(self.lot_min, min(calculated_lot, self.lot_max))

        self.logger.info("Lot calculado: {:.3f} (risco base ${:.2f}, pip_value: {:.5f})".format(final_lot, risk_per_trade, self.pip_value))
        return round(final_lot, 3)

    def execute_trade(self, direction, entry_price):
        """Executa trade automaticamente"""
        try:
            if direction == "BUY":
                sl_price = entry_price - (self.sl_points * self.pip_value)  # Usa pip_value correto
                tp_price = entry_price + (self.tp_points * self.pip_value)
            else:
                sl_price = entry_price + (self.sl_points * self.pip_value)
                tp_price = entry_price - (self.tp_points * self.pip_value)

            lot_size = self.calculate_lot_size()

            # Verifica margem disponível
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                self.logger.error("Informações do símbolo {} não disponíveis".format(self.symbol))
                return False

            # Calcula margem necessária
            margin_required = symbol_info.margin_initial * lot_size
            if self.account_margin < margin_required * 1.2:
                self.logger.warning("Margem insuficiente: ${:.2f} < ${:.2f}".format(self.account_margin, margin_required*1.2))
                return False

            # Prepara ordem
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "type": mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL,
                "volume": lot_size,
                "price": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "comment": "CONSERVATIVE_SCALP_{}_{}".format(self.symbol.upper(), direction),
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Executa
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

                self.logger.info("TRADE EXECUTADO: {} {}".format(direction, self.symbol))
                self.logger.info("   Ticket: {}".format(result.order))
                self.logger.info("   Entrada: {:.5f}".format(entry_price))
                self.logger.info("   SL: {:.5f}".format(sl_price))
                self.logger.info("   TP: {:.5f}".format(tp_price))
                self.logger.info("   Lot: {:.3f}".format(lot_size))

                return True
            else:
                self.logger.error("Falha na execução: {} - {}".format(result.retcode, result.comment))
                return False

        except Exception as e:
            self.logger.error("Erro na execução: {}".format(e))
            return False

    def check_positions(self):
        """Verifica posições abertas e atualiza P&L"""
        if not self.positions_open:
            return

        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return

        # Converte para dicionário por ticket
        active_tickets = {pos.ticket for pos in positions if pos.symbol == self.symbol}

        # Remove posições fechadas e calcula P&L
        for i in range(len(self.positions_open) - 1, -1, -1):
            pos = self.positions_open[i]
            if pos['ticket'] not in active_tickets:
                # Posição fechada
                deals = mt5.history_deals_get(ticket=pos['ticket'])
                if deals:
                    pnl = sum(deal.profit for deal in deals if deal.ticket == pos['ticket'])
                    self.daily_pnl += pnl

                    if pnl > 0:
                        self.consecutive_wins += 1
                        self.consecutive_losses = 0
                        self.logger.info("WIN +${:.2f}".format(pnl))
                    else:
                        self.consecutive_losses += 1
                        self.consecutive_wins = 0
                        self.logger.warning("LOSS ${:.2f}".format(pnl))
                    self.logger.info("Status: Wins consecutivos: {}, Losses: {}".format(self.consecutive_wins, self.consecutive_losses))
                    self.logger.info("P&L Diario: ${:.2f}".format(self.daily_pnl))
                self.positions_open.pop(i)

        # Verifica limite diário
        if abs(self.daily_pnl) >= self.max_daily_loss:
            self.logger.error("Limite diario excedido: ${:.2f} >= ${:.2f}".format(abs(self.daily_pnl), self.max_daily_loss))
            self.stop()

    def main_loop(self):
        """Loop principal da estratégia"""
        self.logger.info("ESTRATEGIA CONSERVATIVA INICIADA PARA {}".format(self.symbol.upper()))
        self.logger.info("Objetivo: ${:.2f} lucro por operacao".format(self.operation_target))
        self.logger.info("Perda maxima: $0.00 (Por simbolo)")
        self.logger.info("Analisando a cada 10 segundos...")

        self.is_running = True

        while self.is_running and not shutdown_event.is_set():
            try:
                # Verifica horário
                if not self.check_trading_hours():
                    time.sleep(300)  # Aguarda 5 minutos fora do horário
                    continue

                # Obtém dados e calcula indicadores
                df = self.get_market_data(50)
                if df is None or len(df) < 50:
                    self.logger.warning("Sem dados suficientes - tentando novamente em 10s")
                    time.sleep(10)
                    continue

                # Calcula indicadores
                df = self.calculate_indicators(df)

                # Log análise
                self.analyze_current_market(df)

                # Verifica condições
                range_ok, range_msg = self.check_range_conditions(df)

                if not range_ok:
                    self.logger.info("Aguardando: {}".format(range_msg))
                    time.sleep(10)
                    continue

                # Procura sinais
                signal, entry_price = self.find_entry_signal(df)

                if signal is None:
                    self.logger.info("Aguardando sinal de entrada perfeito...")
                    time.sleep(10)
                    continue

                # Executa trade
                self.logger.info("SETUP PERFEITO ENCONTRADO: {} @ {:.5f}".format(signal, entry_price))

                if self.execute_trade(signal, entry_price):
                    self.logger.info("trade executado com sucesso!")
                else:
                    self.logger.error("Falha na execução do trade")

                # Pequena pausa
                time.sleep(60)

                # Verifica posições
                self.check_positions()

                # Limite consecutivas
                if self.consecutive_losses >= self.max_consecutive_losses:
                    self.logger.warning("3 perdas consecutivas - pausa automatica por 1 hora")
                    time.sleep(3600)

            except KeyboardInterrupt:
                self.logger.info("Estrategia interrompida pelo usuario")
                self.stop()
                break
            except Exception as e:
                self.logger.error("Erro no loop principal: {}".format(e))
                time.sleep(30)

    def analyze_current_market(self, df):
        """Analisa condições atuais"""
        last = df.iloc[-1]

        # Score percentual
        market_ideal_score = self.calculate_market_ideal_score(df)

        self.logger.info("=" * 50)
        self.logger.info("ANALISE DE MERCADO ATUAL - {} - CONDICOES IDEAIS {:.0f}%".format(self.symbol.upper(), market_ideal_score))
        self.logger.info("=" * 50)

        # Parâmetros
        self.logger.info("[PARAMETROS DA ESTRATEGIA]")
        self.logger.info("Stop Loss: {} pontos".format(self.sl_points))
        self.logger.info("Take Profit: {} pontos".format(self.tp_points))
        self.logger.info("Range BB Target: {}-{} pontos".format(self.bb_range_min, self.bb_range_max))
        self.logger.info("RSI Target: {}-{}".format(self.rsi_neutral_low, self.rsi_neutral_high))
        self.logger.info("Objetivo: ${:.2f} lucro por operacao".format(self.operation_target))

        # Dados de preço atual
        self.logger.info("[DADOS DE PRECO ATUAL]")
        self.logger.info("Preco Atual: {:.5f}".format(last['close']))
        self.logger.info("Preco Maximo: {:.5f}".format(last['high']))
        self.logger.info("Preco Minimo: {:.5f}".format(last['low']))
        self.logger.info("Volume: {}".format(int(last['tick_volume'])))

        # Indicadores
        try:
            self.logger.info("[INDICADORES TECNICOS]")
            bb_range = last['BB_upper'] - last['BB_lower']
            self.logger.info("Bollinger Superior: {:.5f}".format(last['BB_upper']))
            self.logger.info("Bollinger Inferior: {:.5f}".format(last['BB_lower']))
            self.logger.info("Range BB Atual: {:.2f} pontos".format(bb_range))
            self.logger.info("Posicao no Range: {:.2f}%".format(last['BB_position'] * 100))
            self.logger.info("RSI Atual: {:.1f}".format(last['RSI']))

            # Verificações
            self.logger.info("[VERIFICACAO DE CONDICOES]")

            range_ok = self.bb_range_min <= bb_range <= self.bb_range_max
            rsi_ok = self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high
            volume_ok = last['volume_ratio'] >= 0.8

            prev_close = df.iloc[-2]['close']
            gap = abs(last['open'] - prev_close)
            gap_ok = gap <= 20

            self.logger.info("OK Range BB ({}-{}): {:.2f} -> {}".format(self.bb_range_min, self.bb_range_max, bb_range, "PASSOU" if range_ok else "REJEITOU"))
            self.logger.info("OK RSI ({}-{}): {:.1f} -> {}".format(self.rsi_neutral_low, self.rsi_neutral_high, last['RSI'], "PASSOU" if rsi_ok else "REJEITOU"))
            self.logger.info("OK Volume (>=0.8): {:.2f} -> {}".format(last['volume_ratio'], "PASSOU" if volume_ok else "REJEITOU"))
            self.logger.info("OK Gap (<=20pts): {:.1f}pt -> {}".format(gap, "PASSOU" if gap_ok else "REJEITOU"))

            status = "CONDICOES IDEAIS PARA TRADE" if all([range_ok, rsi_ok, volume_ok, gap_ok]) else "AGUARDANDO MELHORAS"
            self.logger.info("STATUS GERAL: {}".format(status))

        except Exception as e:
            self.logger.error("Erro ao calcular indicadores: {}".format(e))

        self.logger.info("=" * 50)

    def stop(self):
        """Para estratégia"""
        self.logger.info("PARANDO ESTRATEGIA CONSERVATIVA PARA {}".format(self.symbol.upper()))
        self.is_running = False

        # Fecha posições
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            for pos in positions:
                if pos.symbol == self.symbol:
                    # Fecha posição
                    self.logger.info("Fechando posicao: {}".format(pos.ticket))

                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": self.symbol,
                        "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                        "position": pos.ticket,
                        "volume": pos.volume,
                        "price": mt5.symbol_info_tick(self.symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(self.symbol).ask,
                        "comment": "EMERGENCY_CLOSE"
                    }

                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        self.logger.info("Posicao {} fechada".format(pos.ticket))

        self.logger.info("P&L Final: ${:.2f}".format(self.daily_pnl))

if __name__ == "__main__":
    main()
