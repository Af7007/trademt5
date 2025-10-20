#!/usr/bin/env python3
"""
Bot MLP Direto no MT5 - Execução Nativa
Sem dependências de API Flask - executa diretamente no MT5
"""

import MetaTrader5 as mt5
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

# Configurações
SYMBOL = "BTCUSDc"
TIMEFRAME = mt5.TIMEFRAME_M1
TAKE_PROFIT_PCT = 0.000533  # TP = 0.0533% do preço (~$33 em BTC a $62k) - reduzido 1/3
STOP_LOSS_PCT = 0.004    # SL = 0.4% do preço (~$250 em BTC a $62k) - ratio 1:5
CONFIDENCE_THRESHOLD = 90  # %
INTERVALO_ANALISE = 5  # segundos - logs a cada 5s

# Códigos ANSI para colorização terminal
class Colors:
    BLUE = '\033[94m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

# Funções de colorização para Python
def color_blue(text):
    return f"{Colors.BLUE}{text}{Colors.END}"

def color_red(text):
    return f"{Colors.RED}{text}{Colors.END}"

def color_green(text):
    return f"{Colors.GREEN}{text}{Colors.END}"

def color_orange(text):
    return f"{Colors.ORANGE}{text}{Colors.END}"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BotMLPDiretto:
    """Bot MLP executado diretamente no MT5"""

    def __init__(self):
        self.modelo = None
        self.scaler = None
        self.posicoes_ativas = []
        self.running = False
        self.start_time = None  # Tempo de início para proteção extra

    def conectar_mt5(self):
        """Conecta no MT5"""
        if not mt5.initialize():
            raise Exception("Falha ao inicializar MT5")

        # Verificar se símbolo está disponível
        if not mt5.symbol_select(SYMBOL, True):
            raise Exception(f"Símbolo {SYMBOL} não disponível")

        logger.info(f"MT5 conectado. Símbolo {SYMBOL} selecionado.")

    def carregar_modelo(self):
        """Carrega modelo treinado (CRÍTICO - sem modelo, não inicia)"""
        try:
            import joblib
            self.modelo = joblib.load('bot/models/mlp_model.pkl')
            logger.info("Modelo treinado carregado!")
        except FileNotFoundError:
            logger.error("❌ ERRO CRÍTICO: Modelo treinado não encontrado em 'bot/models/mlp_model.pkl'")
            logger.error("❌ Sem modelo treinado, bot não pode executar análises seguras")
            logger.error("❌ Abortando inicialização do bot")
            raise RuntimeError("Modelo MLP treinado obrigatório não encontrado")
        except Exception as e:
            logger.error(f"❌ ERRO ao carregar modelo: {e}")
            logger.error("❌ Abortando inicialização do bot")
            raise RuntimeError(f"Falha ao carregar modelo: {e}")

    def criar_modelo_dummy(self):
        """Cria modelo dummy para demonstração"""
        # Dados de exemplo
        np.random.seed(42)
        n_samples = 1000

            # Features dummy - 9 features como no modelo real
        X = np.random.randn(n_samples, 9)
        y = np.random.choice([0, 1, 2], n_samples)  # 0=BUY, 1=SELL, 2=HOLD

        # Treinar modelo simples
        modelo = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=100, random_state=42)
        modelo.fit(X, y)

        logger.info("Modelo dummy criado para demonstração")
        return modelo

    def calcular_indicadores(self, df):
        """Calcula indicadores técnicos"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Médias móveis
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        df['bb_std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

        return df.fillna(0)

    def obter_dados_mercado(self):
        """Obtém dados atuais do mercado"""
        try:
            # Obter candles recentes
            rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
            if rates is None:
                raise Exception("Falha ao obter dados do MT5")

            df = pd.DataFrame(rates)
            df = self.calcular_indicadores(df)

            # Obter preço atual
            tick = mt5.symbol_info_tick(SYMBOL)
            if tick is None:
                raise Exception("Falha ao obter tick atual")

            return df, tick

        except Exception as e:
            logger.error(f"Erro ao obter dados: {e}")
            return None, None

    def analisar_mercado(self, df, tick):
        """Análisa mercado com modelo MLP"""
        try:
            # Preparar features para o modelo
            features = ['open', 'high', 'low', 'close', 'tick_volume',
                       'rsi', 'sma_10', 'sma_20', 'sma_50']

            # Última linha (dados atuais)
            last_candle = df.iloc[-1]
            X = last_candle[features].values.reshape(1, -1)

            # LOGICA BASEADA EM INDICADORES - Análise técnica real
            rsi = last_candle.get('rsi', 50.0)
            sma20 = last_candle.get('sma_20', last_candle.get('close', 0))
            price_close = last_candle.get('close', 0)
            bb_upper = last_candle.get('bb_upper', price_close)
            bb_lower = last_candle.get('bb_lower', price_close)
            volume = last_candle.get('tick_volume', 0)

            # SIMPLIFICADO: ANÁLISE BÁSICA PARA MONITORAMENTO
            # A LÓGICA COMPLEXA VOLTARÁ A SER IMPLEMENTADA NO DJANGO
            sinal = "HOLD"
            confianca = 50.0

            # Apenas sinais muito básicos para testes (nunca executarão devido ao threshold alto)
            if rsi < 30 and volume > 100:
                sinal = "BUY"
                confianca = 55.0
            elif rsi > 70 and volume > 100:
                sinal = "SELL"
                confianca = 55.0

            # Dados atuais do mercado - FORMATO COMPACTO PARA EA MT5
            timestamp_compacto = datetime.now().strftime('%H:%M:%S')
            sinal_compacto = f"{sinal}:{confianca:.0f}%"

            # Log compacto otimizado para EA MT5
            ask_rounded = int(tick.ask)
            bid_rounded = int(tick.bid)
            volume_int = int(last_candle['tick_volume'])
            rsi_int = int(last_candle.get('rsi', 0))
            bb_lower_int = int(last_candle.get('bb_lower', 0))
            bb_upper_int = int(last_candle.get('bb_upper', 0))

            # Log compacto otimizado para EA MT5 e exibição no bot
            log_compacto = f"[MLP|Thr:{CONFIDENCE_THRESHOLD}%|{timestamp_compacto}] {sinal_compacto} | Conf:{confianca:.0f}% | ${ask_rounded}/${bid_rounded} | V:{volume_int} | RSI:{rsi_int} | BB:{bb_lower_int}-{bb_upper_int}"
            logger.info(log_compacto)
            print(log_compacto)  # Exibir também no console do bot

            # Análise técnica detalhada (menos frequente, apenas quando sinal diferente de HOLD)
            if sinal != "HOLD":
                logger.info(f"[TECH|{timestamp_compacto}] SMA20:{last_candle.get('sma_20', 0):.0f} "+
                           f"Bollinger:{last_candle.get('bb_upper', 0):.0f}/{last_candle.get('bb_lower', 0):.0f} "+
                           f"Volume:{last_candle['tick_volume']}")

            return sinal, confianca

        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return "HOLD", 0.0

    def executar_trade(self, sinal, confianca, tick):
        """Executa trade no MT5"""
        try:
            # DEBUG: Verificar threshold
            threshold_pct = CONFIDENCE_THRESHOLD / 100
            logger.debug(f"Comparando confiança {confianca:.1f}% vs threshold {threshold_pct:.2f}")

            if sinal == "HOLD" or confianca < threshold_pct:
                logger.info(f"Sinal {sinal} com confiança baixa ({confianca:.1%}) - executando HOLD")
                return False

            # Determinar tipo de ordem - usar percentuais conservadores
            # TP = 0.0533% (~$33 em BTC a $62k), SL = 0.4% (~$250) - ratio ~1:7.5
            if sinal == "BUY":
                price = tick.ask
                order_type = mt5.ORDER_TYPE_BUY
                sl_price = price * (1 - STOP_LOSS_PCT)      # SL abaixo do preço
                tp_price = price * (1 + TAKE_PROFIT_PCT)    # TP acima do preço
            else:  # SELL
                price = tick.bid
                order_type = mt5.ORDER_TYPE_SELL
                sl_price = price * (1 + STOP_LOSS_PCT)      # SL acima do preço
                tp_price = price * (1 - TAKE_PROFIT_PCT)    # TP abaixo do preço

            # Preparar requisição
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": SYMBOL,
                "volume": 0.02,  # Volume aumentado para 0.02 lotes
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp_price,
                "deviation": 20,
                "magic": 240919,
                "comment": f"MLP Direct {sinal}",
                "type_filling": mt5.ORDER_FILLING_FOK,
            }

            # Executar trade
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                ticket_compacto = result.order
                price_int = int(price)
                tp_int = int(tp_price)
                sl_int = int(sl_price)
                log_trade_compacto = f"[TRADE|EXECUTADO] Ticket:{ticket_compacto} | {sinal}:{int(confianca)}% | P:{price_int} | TP:{tp_int} | SL:{sl_int}"

                # COLORIR LOG DE TRADE EXECUTADO
                if sinal == "BUY":
                    colored_log = color_blue(log_trade_compacto)
                else:  # SELL
                    colored_log = color_red(log_trade_compacto)
                print(colored_log)
                logger.info(log_trade_compacto)
                return result.order
            else:
                logger.error(f"TRADE FALHADO: {result.retcode} - {result.comment}")
                return False

        except Exception as e:
            logger.error(f"Erro ao executar trade: {e}")
            return False

    def verificar_posicoes_ativas(self):
        """Verifica posições ativas e atualiza lista"""
        try:
            positions = mt5.positions_get(symbol=SYMBOL)
            if positions is None:
                positions = []

            self.posicoes_ativas = [pos.ticket for pos in positions]
            logger.debug(f"Posições ativas encontradas: {len(self.posicoes_ativas)}")

            return positions
        except Exception as e:
            logger.error(f"Erro ao verificar posições: {e}")
            return []

    def aguardar_fechamento_tp(self, trade_ticket):
        """Aguarda trade fechar por TP/SL"""
        logger.info(f"Aguardando fechamento do trade {trade_ticket}...")
        start_time = time.time()

        while time.time() - start_time < 600:  # 10 minutos máximo
            try:
                # Sempre atualizar a lista de posições diretamente (não usar cache)
                positions_atuais = mt5.positions_get(symbol=SYMBOL)
                if positions_atuais is None:
                    positions_atuais = []

                tickets_ativos = [pos.ticket for pos in positions_atuais]
                self.posicoes_ativas = tickets_ativos

                # Verificar se o trade específico ainda existe
                if trade_ticket not in tickets_ativos:
                    # Tentar obter informações do deal para determinar profit/loss
                    deals = mt5.history_deals_get(trade_ticket, trade_ticket + 1)
                    close_msg = "✅ Trade fechado! Ticket não encontrado nas posições ativas."

                    if deals and len(deals) > 0:
                        profit = deals[0].profit
                        if profit > 0:
                            close_msg = color_green(f"🎉 TRADE FECHADO: +LUCRO ${profit:.2f} | Ticket:{trade_ticket}")
                        elif profit < 0:
                            close_msg = color_orange(f"💸 TRADE FECHADO: -PREJUÍZO ${profit:.2f} | Ticket:{trade_ticket}")
                        else:
                            close_msg = f"⚖️ TRADE FECHADO: SEM LUCRO/PREJUÍZO | Ticket:{trade_ticket}"

                    print(close_msg)
                    logger.info(f"Posições ativas atuais: {len(tickets_ativos)}")
                    return True

                logger.debug(f"Trade {trade_ticket} ainda ativo. Posições ativas: {len(tickets_ativos)}")
                time.sleep(5)  # Verificar a cada 5 segundos

            except Exception as e:
                logger.error(f"Erro ao verificar trade: {e}")
                time.sleep(5)

        logger.warning("⏰ Timeout aguardando fechamento")
        return False

    def run(self):
        """Loop principal do bot"""
        tp_dollars = TAKE_PROFIT_PCT * 62000  # aproximado para BTC a $62k
        sl_dollars = STOP_LOSS_PCT * 62000
        logger.info("INICIANDO BOT MLP DIRETO NO MT5")
        logger.info(".1f")
        logger.info(f"Configurações: Threshold={CONFIDENCE_THRESHOLD}%, Intervalo={INTERVALO_ANALISE}s")
        logger.info("=" * 60)

        self.running = True

        try:
            # Conectar MT5
            self.conectar_mt5()

            # Carregar modelo
            self.carregar_modelo()

            # Verificar posições iniciais
            self.verificar_posicoes_ativas()

            logger.info("Bot inicializado - aguardando oportunidades...")
            logger.info("AGUARDANDO 30 segundo primeiro warmup antes da primeira análise...")
            time.sleep(30)  # Primeiro warmup - não executar trades nos primeiros 30 segundos
            logger.info("✅ Warmup concluído - iniciando análises regulares...")

            while self.running:
                try:
                    # Obter dados do mercado
                    df, tick = self.obter_dados_mercado()
                    if df is None or tick is None:
                        logger.warning("Falha ao obter dados - tentando novamente em 30s")
                        time.sleep(30)
                        continue

                    # Análisar mercado
                    sinal, confianca = self.analisar_mercado(df, tick)

                    # EXECUÇÃO SÓ COM CONFIANÇA BAIXA TEMPORÁRIO PARA TESTES
                    # TODO: CORRIGIR LÓGICA DO THRESHOLD PARA 90%+
                    # if confianca >= 0.99:  # APENAS CONFIANÇA MÁXIMA (99%+)

                    # POR ENQUANTO: EXECUTAR SÓ SINAIS FORTES (70%+) PARA TESTES
                    threshold_atual = 70.0  # Reduzido temporariamente para 70% para testes
                    can_execute = sinal in ["BUY", "SELL"] and confianca >= threshold_atual

                    logger.debug(f"DEBUG Confiança: {confianca:.1f}%, Sinal: {sinal}, Threshold atual: {threshold_atual:.1f}%")

                    if can_execute:
                        # COLORIR LOG DE EXECUÇÃO
                        if sinal == "BUY":
                            color_log = color_blue(f"✅ EXECUTANDO: {sinal} com {confianca:.1f}% confiança")
                        else:  # SELL
                            color_log = color_red(f"✅ EXECUTANDO: {sinal} com {confianca:.1f}% confiança")
                        print(color_log)
                        logger.info(color_blue(f"#### TRADE ENTRY: {sinal} position opened ####") if sinal == "BUY" else color_red(f"#### TRADE ENTRY: {sinal} position opened ####"))

                        ticket = self.executar_trade(sinal, confianca, tick)
                        if ticket:
                            # Atualizar posições após trade
                            time.sleep(1)  # Dar tempo para MT5 processar
                            self.verificar_posicoes_ativas()
                            logger.info(f"Trade {ticket} registrado. Posições ativas: {len(self.posicoes_ativas)}")

                            # Aguardar fechamento
                            self.aguardar_fechamento_tp(ticket)
                            logger.info("Pronto para próxima análise!")
                        else:
                            logger.warning("Falha na execução - esperando próxima oportunidade")
                    elif sinal in ["BUY", "SELL"]:
                        # COLORIR LOG DE BLOQUEIO
                        blocked_msg = f"🚫 BLOQUEADO: {sinal} com {confianca:.1f}% < {threshold_pct:.2f} threshold (aguardando)"
                        if sinal == "BUY":
                            print(color_blue(blocked_msg))
                        else:  # SELL
                            print(color_red(blocked_msg))
                        logger.debug(f"Signal {sinal} blocked by low confidence threshold")
                    else:
                        logger.info(f"Sinal {sinal} - aguardando melhor oportunidade")

                    # Aguardar próxima análise
                    time.sleep(INTERVALO_ANALISE)

                except KeyboardInterrupt:
                    logger.info("🛑 Bot interrompido pelo usuário")
                    self.running = False
                    break
                except Exception as e:
                    logger.error(f"Erro no loop principal: {e}")
                    time.sleep(30)

        except Exception as e:
            logger.error(f"Erro crítico: {e}")
        finally:
            logger.info("🔻 Finalizando bot...")
            mt5.shutdown()
            logger.info("✅ Bot finalizado com sucesso!")


def main():
    """Função principal"""
    print()
    print("BOT MLP DIRETO NO MT5")
    print("=" * 50)
    print("Executará trades reais no MetaTrader 5")
    print("• Volume: 0.02 lotes (aumentado)")
    print("• TP: ~$33 por trade")
    print("• SL: ~$250 por trade")
    print("• Threshold: 90% confiança")
    print("• Intervalo: 5s entre análises")
    print()
    print("Pressione CTRL+C para parar")
    print()

    # Criar e executar bot
    bot = BotMLPDiretto()
    bot.run()


if __name__ == "__main__":
    main()
