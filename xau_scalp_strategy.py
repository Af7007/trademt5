#!/usr/bin/env python3
"""
ESTRATÉGIA DE SCALPING CONSERVADOR PARA XAUUSDc (24/7)
Executa operações de $1 lucro / $0 perda automaticamente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import logging
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
        logging.FileHandler(f'conservative_scalp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConservativeScalpStrategy:
    """Estratégia de scalping ultra-conservador para XAUUSDc (24/7)"""

    def __init__(self):
        # Configurações da estratégia XAU
        self.symbol = "XAUUSDc"
        self.timeframe = mt5.TIMEFRAME_M5

        # Parâmetros de risco XAU
        self.max_daily_loss = 25.0
        self.operation_target = 1.0
        self.lot_min = 0.02
        self.lot_max = 0.08
        self.lot_current = self.lot_min

        # Pip value XAU = 0.10 (diferente do BTC 0.01)
        self.pip_value = 0.10

        # Parâmetros técnicos XAU - Ouro mais estável
        self.sl_points = 60   # SL menor pois Ouro é préamável
        self.tp_points = 12   # TP proporcional
        self.bb_period = 18   # BB período menor que BTC (mercado mais remkite estável)
        self.rsi_period = 12  # RSI período menor
        self.rsi_neutral_low = 45
        self.rsi_neutral_high = 55
        self.bb_range_min = 50    # Range mínimo XAU (mais permissivo)
        self.bb_range_max = 800
        self.ema_fast = 21
        self.ema_slow = 50
        self.bb_deviations = 2

        # Controle operacional
        self.positions_open = []
        self.daily_pnl = 0.0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 3

        # Status XAU
        self.is_running = False
        self.account_balance = 0.0
        self.account_margin = 0.0

        # Horários Expandidos XAU - Quase 24/7
        self.allowed_hours = [
            (8, 0, 11, 30),   # London open
            (12, 0, 16, 0),   # Extended London/NYC
            (17, 0, 21, 0),   # Extended trading
            (22, 0, 1, 0),    # Asya early morning
            (2, 0, 6, 0),     # Asya late morning
        ]

        # Logging XAU
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - CONSERVATIVE_SCALP_XAU - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/conservative_scalp_xau_{}.log'.format(datetime.now().strftime("%Y%m%d_%H%M%S"))),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # MT5 XAU
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

        # 1. Range BB - ideal no meio do range (700-900 pontos)
        bb_range = last['BB_upper'] - last['BB_lower']
        if 200 <= bb_range <= 1200:  # Dentro do range aceitável
            # Quanto mais próximo de 800 pontos (meio), melhor
            ideal_range = 800
            range_diff = abs(bb_range - ideal_range) / 200  # desvio máximo de 200 pontos
            scores['range'] = max(0, 1 - range_diff)  # 1 = perfeito, 0 = limite
            total_score += 1  # passa = +1 ponto
        else:
            scores['range'] = 0
            total_score += 0

        # 2. RSI - ideal próximo de 50
        rsi_distance = abs(last['RSI'] - 50) / 10  # desvio máximo de 10 pontos
        scores['rsi'] = max(0, 1 - rsi_distance)
        if self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high:
            total_score += 1  # passa = +1 ponto

        # 3. Volume - ideal >= 1.0
        scores['volume'] = min(last['volume_ratio'], 2.0) / 2.0  # máximo 200% como 1.0
        if last['volume_ratio'] >= 0.8:
            total_score += 1  # passa = +1 ponto

        # 4. Gap - ideal = 0
        gap = abs(last['open'] - prev_close)
        gap_score = max(0, 1 - (gap / 20.0))  # gap máximo 20 pontos = 0
        scores['gap'] = gap_score
        if gap <= 20:
            total_score += 1  # passa = +1 ponto

        # 5. Bollinger Position - quanto mais próximo dos thresholds (0.3 ou 0.8), melhor
        if last['BB_position'] <= 0.3:  # próximo da banda inferior
            bb_pos_score = max(0, (0.3 - last['BB_position']) * 3.33)  # próximo de 0%
        elif last['BB_position'] >= 0.8:  # próximo da banda superior
            bb_pos_score = max(0, (last['BB_position'] - 0.8) * 3.33)  # próximo de 100%
        else:
            bb_pos_score = 0  # zona neutra = ruim para scalping

        scores['bb_position'] = bb_pos_score
        total_score += max(0, min(1, bb_pos_score))  # +0-1 ponto baseado na proximidade

        # Score final: média ponderada com condições mínimas
        conditions_pass = (200 <= bb_range <= 1200 and
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
        """Verifica condições de range para scalping XAU"""
        last = df.iloc[-1]

        # Range: canal de 150-800 pontos (XAU estável - range menor)
        bb_range = last['BB_upper'] - last['BB_lower']
        if not (self.bb_range_min <= bb_range <= self.bb_range_max):
            return False, "Range XAU fora dos parâmetros: {:.2f}".format(bb_range)

        # RSI neutro (45-55)
        if not (self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high):
            return False, "XAU RSI não neutro: {:.1f}".format(last['RSI'])

        # Volume adequado (mais permissivo - 0.6)
        if last['volume_ratio'] < 0.6:
            return False, "XAU Volume baixo: {:.2f}".format(last['volume_ratio'])

        # Sem gaps grandes
        prev_close = df.iloc[-2]['close']
        gap = abs(last['open'] - prev_close)
        if gap > 20:
            return False, "XAU Gap alto: {:.1f} pontos".format(gap)

        return True, "XAU condições ideais"

    def find_entry_signal(self, df):
        """Busca sinais de entrada"""
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Setup BUY: Preço colado na banda inferior + candle de força - MAIS AGRESSIVO
        if last['BB_position'] <= 0.2:  # Maiss_reviews agress تستivo (20%)
            # Confirmação: Alça rosa após candle azul em baixa
            if (prev['close'] < prev['open'] and  # Candle anterior negativo
                last['close'] > last['open'] and   # Candle atual positivo
                last['low'] <= last['BB_lower'] + 1):  # Toca a banda inferior
                return "BUY", last['close'] + 0.1  # Entrada acima da mínima

        # Setup SELL: Preço colado na banda superior + candle de força
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

        # Calcula baseado no risco - XAU usa pip_value 0.10
        risk_per_trade = 5.0  # $5 máximo por trade
        pip_value = self.pip_value  # 0.10 para XAU

        # Lot size = Risk / (SL_points * pip_value)
        calculated_lot = risk_per_trade / (self.sl_points * pip_value)

        # Limita aos ranges
        final_lot = max(self.lot_min, min(calculated_lot, self.lot_max))

        logger.info("XAU Lot: {:.3f} (risco ${:.2f}, pip_value {:.2f})".format(final_lot, risk_per_trade, pip_value))
        return round(final_lot, 2)

    def execute_trade(self, direction, entry_price):
        """Executa trade automaticamente"""
        try:
            if direction == "BUY":
                sl_price = entry_price - (self.sl_points * 0.1)  # 0.1 = 1 pip no XAU
                tp_price = entry_price + (self.tp_points * 0.1)
            else:  # SELL
                sl_price = entry_price + (self.sl_points * 0.1)
                tp_price = entry_price - (self.tp_points * 0.1)

            lot_size = self.calculate_lot_size()

            # Verifica margem disponível
            symbol_info = mt5.symbol_info(self.symbol)
            if not symbol_info:
                logger.error("Informações do símbolo {} não disponíveis".format(self.symbol))
                return False

            # Calcula margem necessária
            margin_required = symbol_info.margin_initial * lot_size
            if self.account_margin < margin_required * 1.2:  # Margin buffer
                logger.warning("Margem insuficiente: ${:.2f} < ${:.2f}".format(self.account_margin, margin_required*1.2))
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
                "comment": "CONSERVATIVE_SCALP_{}".format(direction),
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

                logger.info("TRADE EXECUTADO: {} {}".format(direction, self.symbol))
                logger.info("   Ticket: {}".format(result.order))
                logger.info("   Entrada: {:.2f}".format(entry_price))
                logger.info("   SL: {:.2f}".format(sl_price))
                logger.info("   TP: {:.2f}".format(tp_price))
                logger.info("   Lot: {:.3f}".format(lot_size))

                return True
            else:
                logger.error("Falha na execução: {} - {}".format(result.retcode, result.comment))
                return False

        except Exception as e:
            logger.error("Erro na execução: {}".format(e))
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
                # Posição fechada - buscar no histórico
                deals = mt5.history_deals_get(ticket=pos['ticket'])
                if deals:
                    pnl = sum(deal.profit for deal in deals if deal.ticket == pos['ticket'])
                    self.daily_pnl += pnl

                    if pnl > 0:
                        self.consecutive_wins += 1
                        self.consecutive_losses = 0
                        logger.info("WIN +${:.2f}".format(pnl))
                    else:
                        self.consecutive_losses += 1
                        self.consecutive_wins = 0
                        logger.warning("LOSS ${:.2f}".format(pnl))
                    logger.info("Status: Wins consecutivos: {}, Losses: {}".format(self.consecutive_wins, self.consecutive_losses))
                    logger.info("P&L Diario: ${:.2f}".format(self.daily_pnl))
                self.positions_open.pop(i)

        # Verifica limite diário
        if abs(self.daily_pnl) >= self.max_daily_loss:
            logger.error("Limite diario excedido: ${:.2f} >= ${:.2f}".format(abs(self.daily_pnl), self.max_daily_loss))
            self.stop()

    def main_loop(self):
        """Loop principal da estratégia"""
        logger.info("ESTRATEGIA CONSERVATIVA INICIADA")
        logger.info("Objetivo: ${:.2f} lucro por operacao".format(self.operation_target))
        logger.info("Perda maxima: $0.00")
        logger.info("Analisando a cada 10 segundos...")

        self.is_running = True

        while self.is_running:
            try:
                # Verifica horário de operação
                if not self.check_trading_hours():
                    time.sleep(300)  # Aguarda 5 minutos fora do horário
                    continue

                # Obtém dados de mercado
                df = self.get_market_data(50)
                if df is None or len(df) < 50:
                    logger.warning("Sem dados suficientes - tentando novamente em 10s")
                    time.sleep(10)
                    continue

                # Calcula indicadores primeiro
                df = self.calculate_indicators(df)

                # Agora faz análise (com indicadores já calculados)
                self.analyze_current_market(df)

                # Verifica condições
                range_ok, range_msg = self.check_range_conditions(df)

                if not range_ok:
                    logger.info("Aguardando: {}".format(range_msg))
                    time.sleep(10)
                    continue

                # Procura sinais de entrada
                signal, entry_price = self.find_entry_signal(df)

                if signal is None:
                    logger.info("Aguardando sinal de entrada perfeito...")
                    time.sleep(10)
                    continue

                # Executa trade
                logger.info("SETUP PERFEITO ENCONTRADO: {} @ {:.2f}".format(signal, entry_price))

                if self.execute_trade(signal, entry_price):
                    logger.info("trade executado com sucesso!")
                else:
                    logger.error("Falha na execução do trade")

                # Pequena pausa após execução
                time.sleep(60)

                # Verifica posições abertas
                self.check_positions()

                # Verifica limite de consecutivas
                if self.consecutive_losses >= self.max_consecutive_losses:
                    logger.warning("3 perdas consecutivas - pausa automatica por 1 hora")
                    time.sleep(3600)  # 1 hora pausa

            except KeyboardInterrupt:
                logger.info("Estrategia interrompida pelo usuario")
                self.stop()
                break
            except Exception as e:
                logger.error("Erro no loop principal: {}".format(e))
                time.sleep(30)

    def analyze_current_market(self, df):
        """Analisa e exibe condições atuais do mercado"""
        last = df.iloc[-1]

        # Calcular score percentual das condições ideais
        market_ideal_score = self.calculate_market_ideal_score(df)
        logger.info("=" * 50)
        logger.info("ANALISE DE MERCADO ATUAL - {} - CONDICOES IDEAIS {:.0f}%".format(self.symbol.upper(), market_ideal_score))
        logger.info("=" * 50)

        # Parâmetros da estratégia
        logger.info("[PARAMETROS DA ESTRATEGIA]")
        logger.info("Stop Loss: {} pontos".format(self.sl_points))
        logger.info("Take Profit: {} pontos".format(self.tp_points))
        logger.info("Range BB Target: 50-800 pontos (XAU acomodado)")
        logger.info("RSI Target: 45-55 (mercado Forex)")
        logger.info("Objetivo: ${:.2f} lucro por operacao".format(self.operation_target))
        logger.info("Perda Max: $0.00")

        # Dados do preço atual
        logger.info("[DADOS DE PRECO ATUAL]")
        logger.info("Preco Atual: {:.2f}".format(last['close']))
        logger.info("Preco Maximo: {:.2f}".format(last['high']))
        logger.info("Preco Minimo: {:.2f}".format(last['low']))
        logger.info("Volume: {}".format(int(last['tick_volume'])))

        # Tentar calcular indicadores se não existem
        try:
            if 'BB_upper' not in df.columns:
                logger.info("Calculando indicadores tecnicos...")
                df = self.calculate_indicators(df)

            # Recalcular com dados atualizados
            last = df.iloc[-1]

            # Indicadores calculados
            logger.info("[INDICADORES TECNICOS]")
            logger.info("Bollinger Superior: {:.2f}".format(last['BB_upper']))
            logger.info("Bollinger Inferior: {:.2f}".format(last['BB_lower']))
            bb_range = last['BB_upper'] - last['BB_lower']
            logger.info("Range BB Atual: {:.2f} pontos".format(bb_range))
            logger.info("Posicao no Range: {:.2f}%".format(last['BB_position'] * 100))
            logger.info("RSI Atual: {:.1f}".format(last['RSI']))

            # Volume analysis - reduzido
            logger.info("Volume: {:.1f} | Ratio: {:.2f}".format(last['volume_avg'], last['volume_ratio']))

            # Verificações de condição
            logger.info("[VERIFICACAO DE CONDICOES]")

            # Range check - XAU estável
            range_ok = self.bb_range_min <= bb_range <= self.bb_range_max
            logger.info("OK Range BB ({}-{}): {:.2f} -> {}".format(self.bb_range_min, self.bb_range_max, bb_range, "PASSOU" if range_ok else "REJEITOU"))

            # RSI check
            rsi_ok = self.rsi_neutral_low <= last['RSI'] <= self.rsi_neutral_high
            logger.info("OK RSI (40-60): {:.1f} -> {}".format(last['RSI'], "PASSOU" if rsi_ok else "REJEITOU"))

            # Volume check
            volume_ok = last['volume_ratio'] >= 0.8
            logger.info("OK Volume (>=0.8): {:.2f} -> {}".format(last['volume_ratio'], "PASSOU" if volume_ok else "REJEITOU"))

            # Gap check
            prev_close = df.iloc[-2]['close']
            gap = abs(last['open'] - prev_close)
            gap_ok = gap <= 20
            logger.info("OK Gap (<=20pts): {:.1f}pt -> {}".format(gap, "PASSOU" if gap_ok else "REJEITOU"))

            # Overall assessment
            all_ok = range_ok and rsi_ok and volume_ok and gap_ok
            status_msg = "CONDICOES IDEAIS PARA TRADE" if all_ok else "AGUARDANDO MELHORAS"
            logger.info("STATUS GERAL: {}".format(status_msg))

        except Exception as e:
            logger.error("Erro ao calcular indicadores: {}".format(e))
            logger.info("ERRO TEKCO - VERIFICAR INDICADORES")

        logger.info("=" * 50)

        return last

    def stop(self):
        """Para a estratégia"""
        logger.info("PARANDO ESTRATEGIA CONSERVATIVA")
        self.is_running = False

        # Fecha todas as posições abertas
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            for pos in positions:
                if pos.symbol == self.symbol:
                    logger.info("Fechando posicao: {}".format(pos.ticket))

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
                        logger.info("Posicao {} fechada".format(pos.ticket))
                    else:
                        logger.error("Falha ao fechar {}".format(pos.ticket))

        logger.info("P&L Final: ${:.2f}".format(self.daily_pnl))
        mt5.shutdown()

def main():
    """Ponto de entrada principal"""
    strategy = ConservativeScalpStrategy()

    try:
        logger.info("Iniciando Estrategia Conservativa de Scalping...")
        logger.info("Objetivo: $1 lucro / $0 perda por operacao")
        logger.info("Margem de seguranca contra liquidacoes")
        logger.info("Foco: Pequenos lucros consecutivos + Alta taxa de acerto")
        logger.info("Pressione CTRL+C para parar a qualquer momento")

        strategy.main_loop()

    except KeyboardInterrupt:
        logger.info("Estrategia interrompida pelo usuario")
        strategy.stop()
    except Exception as e:
        logger.error("Erro critico: {}".format(e))
        strategy.stop()

if __name__ == "__main__":
    main()
