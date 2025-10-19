"""
Scalping Bot - Sistema de Trading Automático para BTC/USD
Executa operações de scalping baseadas em análise de padrões com confiança > 85%
"""

import MetaTrader5 as mt5
import time
import logging
from datetime import datetime
from pattern_analyzer import analyze_market
import pandas as pd

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scalping_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ScalpingBot')


class ScalpingBot:
    """
    Bot de Scalping Automático para BTC/USD

    Estratégia:
    - Entra em operações quando confiança > 85%
    - Stop Loss: 0.5% do preço de entrada
    - Take Profit: 0.3% do preço de entrada (scalping)
    - Gerenciamento de risco: máximo de 3 posições simultâneas
    """

    def __init__(self, symbol="BTCUSDc", timeframe=mt5.TIMEFRAME_M5,
                 confidence_threshold=85, volume=0.01, use_dynamic_risk=True):
        """
        Inicializa o bot de scalping

        Args:
            symbol: Símbolo para trading (padrão: BTCUSDc)
            timeframe: Timeframe para análise (padrão: M5)
            confidence_threshold: Confiança mínima para entrada (padrão: 85%)
            volume: Volume da operação em lotes (padrão: 0.01)
            use_dynamic_risk: Usar gerenciamento de risco dinâmico (padrão: True)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.confidence_threshold = confidence_threshold
        self.volume = volume
        self.max_positions = 3
        self.running = False
        self.use_dynamic_risk = use_dynamic_risk

        # Parâmetros de risco
        if use_dynamic_risk:
            # Risco dinâmico baseado na banca
            self.max_loss_per_trade = 0.20  # 20% da banca máximo por trade
            self.target_profit_per_trade = 0.50  # $0.50 de lucro alvo por trade
            # Manter valores padrão para compatibilidade
            self.stop_loss_pct = 0.5
            self.take_profit_pct = 0.3
        else:
            # Risco percentual fixo (padrão anterior)
            self.stop_loss_pct = 0.5  # 0.5% de stop loss
            self.take_profit_pct = 0.3  # 0.3% de take profit (scalping)

        # Controle de operações
        self.max_positions = 1  # Máximo 1 posição por vez
        self.min_time_between_trades = 300  # 5 minutos entre operações
        self.last_trade_time = None

        # Estatísticas
        self.stats = {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'total_profit': 0.0,
            'last_signal_time': None
        }

        logger.info(f"ScalpingBot inicializado - {symbol} {timeframe}")
        logger.info(f"Confiança mínima: {confidence_threshold}%")
        logger.info(f"Volume: {volume} lotes")
        logger.info(f"Máximo posições: {self.max_positions}")
        logger.info(f"Intervalo mínimo entre trades: {self.min_time_between_trades}s")
        if use_dynamic_risk:
            logger.info(f"Modo: Risco dinâmico (20% banca | Lucro alvo: ${self.target_profit_per_trade})")
        else:
            logger.info(f"Modo: Risco percentual (SL: {self.stop_loss_pct}% | TP: {self.take_profit_pct}%)")


    def initialize_mt5(self):
        """Inicializa conexão com MT5"""
        if not mt5.initialize():
            logger.error("Falha ao inicializar MT5")
            return False

        # Verificar se o símbolo está disponível
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            logger.error(f"Símbolo {self.symbol} não encontrado")
            return False

        # Habilitar símbolo para trading
        if not symbol_info.visible:
            if not mt5.symbol_select(self.symbol, True):
                logger.error(f"Falha ao selecionar símbolo {self.symbol}")
                return False

        logger.info("MT5 inicializado com sucesso")
        return True


    def get_market_analysis(self):
        """
        Obtém análise do mercado usando o pattern analyzer

        Returns:
            dict: Análise completa com sinal, confiança, etc.
        """
        try:
            # Obter dados históricos
            rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 100)
            if rates is None or len(rates) == 0:
                logger.warning("Sem dados de mercado disponíveis")
                return None

            # Converter para DataFrame
            df = pd.DataFrame(rates)

            # Calcular indicadores
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()

            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.set_index('time')

            # Executar análise
            analysis = analyze_market(df)

            return analysis

        except Exception as e:
            logger.error(f"Erro ao obter análise de mercado: {e}")
            import traceback
            traceback.print_exc()
            return None


    def get_current_positions_count(self):
        """Retorna número de posições abertas para o símbolo"""
        positions = mt5.positions_get(symbol=self.symbol)
        return len(positions) if positions else 0


    def calculate_sl_tp(self, entry_price, order_type):
        """
        Calcula Stop Loss e Take Profit baseado no preço de entrada

        Args:
            entry_price: Preço de entrada da ordem
            order_type: Tipo da ordem (BUY ou SELL)

        Returns:
            tuple: (stop_loss, take_profit)
        """
        if self.use_dynamic_risk:
            return self.calculate_dynamic_sl_tp(entry_price, order_type)
        else:
            return self.calculate_percentage_sl_tp(entry_price, order_type)

    def calculate_percentage_sl_tp(self, entry_price, order_type):
        """
        Calcula SL e TP baseado em percentual fixo (modo antigo)

        Args:
            entry_price: Preço de entrada da ordem
            order_type: Tipo da ordem (BUY ou SELL)

        Returns:
            tuple: (stop_loss, take_profit)
        """
        if order_type == "BUY":
            stop_loss = entry_price * (1 - self.stop_loss_pct / 100)
            take_profit = entry_price * (1 + self.take_profit_pct / 100)
        else:  # SELL
            stop_loss = entry_price * (1 + self.stop_loss_pct / 100)
            take_profit = entry_price * (1 - self.take_profit_pct / 100)

        return stop_loss, take_profit

    def calculate_dynamic_sl_tp(self, entry_price, order_type):
        """
        Calcula SL e TP baseado na banca (modo dinâmico)

        Args:
            entry_price: Preço de entrada da ordem
            order_type: Tipo da ordem (BUY ou SELL)

        Returns:
            tuple: (stop_loss, take_profit)
        """
        try:
            # Obter informações da conta
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("Não foi possível obter informações da conta, usando modo percentual")
                return self.calculate_percentage_sl_tp(entry_price, order_type)

            account_balance = account_info.balance
            max_loss_per_trade = account_balance * self.max_loss_per_trade

            # Para BTCUSD, calcular movimento necessário
            loss_per_lot_per_dollar = 0.01  # $0.01 por lote por $1 de movimento
            max_price_movement_down = max_loss_per_trade / loss_per_lot_per_dollar

            # Calcular TP para lucro alvo
            profit_per_lot_per_dollar = 0.01
            price_movement_up = self.target_profit_per_trade / profit_per_lot_per_dollar

            if order_type == "BUY":
                stop_loss = entry_price - max_price_movement_down
                take_profit = entry_price + price_movement_up
            else:  # SELL
                stop_loss = entry_price + max_price_movement_down
                take_profit = entry_price - price_movement_up

            logger.info(f"SL Dinâmico: ${stop_loss:.2f} | TP Dinâmico: ${take_profit:.2f}")
            logger.info(f"Banca: ${account_balance:.2f} | Max perda: ${max_loss_per_trade:.2f}")

            return stop_loss, take_profit

        except Exception as e:
            logger.error(f"Erro ao calcular SL/TP dinâmico: {e}")
            logger.warning("Usando modo percentual como fallback")
            return self.calculate_percentage_sl_tp(entry_price, order_type)


    def execute_trade(self, signal, confidence, current_price):
        """
        Executa uma operação de trading

        Args:
            signal: Tipo de sinal (BUY ou SELL)
            confidence: Confiança do sinal (0-100)
            current_price: Preço atual do ativo

        Returns:
            bool: True se operação foi executada com sucesso
        """
        try:
            # Verificar número de posições abertas
            positions_count = self.get_current_positions_count()
            if positions_count >= self.max_positions:
                logger.warning(f"Máximo de {self.max_positions} posições já abertas. Aguardando...")
                return False

            # Determinar tipo de ordem
            order_type = mt5.ORDER_TYPE_BUY if signal == "BUY" else mt5.ORDER_TYPE_SELL

            # Calcular SL e TP
            sl, tp = self.calculate_sl_tp(current_price, signal)

            # Obter informações do símbolo
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                logger.error(f"Falha ao obter informações do símbolo {self.symbol}")
                return False

            # Preparar requisição de ordem
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": self.volume,
                "type": order_type,
                "price": current_price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": f"Scalping Bot - Conf: {confidence}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Enviar ordem
            logger.info(f"Enviando ordem {signal} para {self.symbol}")
            logger.info(f"Preço: {current_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")

            result = mt5.order_send(request)

            if result is None:
                logger.error("Falha ao enviar ordem - resultado None")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Ordem falhou: {result.retcode} - {result.comment}")
                return False

            # Ordem executada com sucesso
            self.stats['total_trades'] += 1
            logger.info(f"✅ Ordem {signal} executada com sucesso!")
            logger.info(f"Ticket: {result.order} | Volume: {result.volume} | Preço: {result.price:.2f}")

            return True

        except Exception as e:
            logger.error(f"Erro ao executar trade: {e}")
            import traceback
            traceback.print_exc()
            return False


    def check_and_execute_signal(self):
        """
        Verifica análise de mercado e executa operação se confiança > threshold

        Returns:
            dict: Resultado da verificação e execução
        """
        # Verificar se há posições abertas
        positions_count = self.get_current_positions_count()
        if positions_count >= self.max_positions:
            return {
                "status": "waiting",
                "message": f"Máximo de {self.max_positions} posição(ões) já aberta(s). Aguardando fechamento...",
                "current_positions": positions_count
            }

        # Verificar tempo mínimo entre operações
        current_time = time.time()
        if (self.last_trade_time and
            current_time - self.last_trade_time < self.min_time_between_trades):
            remaining_time = self.min_time_between_trades - (current_time - self.last_trade_time)
            return {
                "status": "waiting",
                "message": f"Aguardando {remaining_time:.0f}s entre operações...",
                "remaining_time": remaining_time
            }

        analysis = self.get_market_analysis()

        if analysis is None:
            return {"status": "error", "message": "Falha ao obter análise de mercado"}

        signal = analysis.get('signal')
        confidence = analysis.get('confidence', 0)
        current_price = analysis.get('current_price', 0)

        result = {
            "status": "analyzed",
            "signal": signal,
            "confidence": confidence,
            "current_price": current_price,
            "timestamp": datetime.now().isoformat(),
            "executed": False
        }

        # Verificar se sinal é válido (BUY ou SELL)
        if signal not in ["BUY", "SELL"]:
            result["message"] = f"Sinal neutro: {signal} (confiança: {confidence}%)"
            logger.info(result["message"])
            return result

        # Verificar confiança
        if confidence < self.confidence_threshold:
            result["message"] = f"Confiança baixa: {confidence}% < {self.confidence_threshold}%"
            logger.info(f"Sinal {signal} com confiança {confidence}% (mín: {self.confidence_threshold}%)")
            return result

        # Confiança alta - executar ordem
        logger.info(f"🎯 SINAL DE ALTA CONFIANÇA DETECTADO!")
        logger.info(f"Tipo: {signal} | Confiança: {confidence}% | Preço: {current_price:.2f}")

        # Executar trade
        success = self.execute_trade(signal, confidence, current_price)

        result["executed"] = success
        if success:
            result["status"] = "executed"
            result["message"] = f"Ordem {signal} executada com confiança {confidence}%"
            self.last_trade_time = current_time  # Registrar tempo da operação
        else:
            result["status"] = "failed"
            result["message"] = "Falha ao executar ordem"

        return result


    def update_stats(self):
        """Atualiza estatísticas do bot baseado em posições fechadas"""
        try:
            # Obter histórico de deals (últimas 100 operações)
            from_date = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7 dias atrás
            deals = mt5.history_deals_get(from_date, datetime.now().timestamp())

            if deals is None or len(deals) == 0:
                return

            # Filtrar apenas deals do bot (pelo magic number)
            bot_deals = [d for d in deals if d.magic == 234000]

            total_profit = sum(d.profit for d in bot_deals)
            wins = sum(1 for d in bot_deals if d.profit > 0)
            losses = sum(1 for d in bot_deals if d.profit < 0)

            self.stats['wins'] = wins
            self.stats['losses'] = losses
            self.stats['total_profit'] = total_profit

        except Exception as e:
            logger.error(f"Erro ao atualizar estatísticas: {e}")


    def get_stats(self):
        """Retorna estatísticas do bot"""
        self.update_stats()

        win_rate = (self.stats['wins'] / self.stats['total_trades'] * 100) if self.stats['total_trades'] > 0 else 0

        return {
            **self.stats,
            'win_rate': win_rate,
            'running': self.running,
            'symbol': self.symbol,
            'confidence_threshold': self.confidence_threshold,
            'current_positions': self.get_current_positions_count(),
            'max_positions': self.max_positions
        }


    def run_once(self):
        """Executa uma verificação única (usado para modo manual)"""
        if not self.initialize_mt5():
            return {"status": "error", "message": "Falha ao inicializar MT5"}

        return self.check_and_execute_signal()


    def run(self, interval=60):
        """
        Executa bot em loop contínuo

        Args:
            interval: Intervalo entre verificações em segundos (padrão: 60s)
        """
        if not self.initialize_mt5():
            logger.error("Não foi possível inicializar MT5. Abortando...")
            return

        self.running = True
        logger.info(f"🤖 Bot iniciado! Verificando sinais a cada {interval} segundos")
        logger.info(f"Confiança mínima para entrada: {self.confidence_threshold}%")

        try:
            while self.running:
                logger.info("=" * 60)
                logger.info("Verificando mercado...")

                result = self.check_and_execute_signal()

                logger.info(f"Resultado: {result.get('message', 'N/A')}")

                # Aguardar intervalo
                logger.info(f"Aguardando {interval} segundos até próxima verificação...")
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\n🛑 Bot interrompido pelo usuário")
            self.running = False
        except Exception as e:
            logger.error(f"Erro crítico no bot: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
        finally:
            mt5.shutdown()
            logger.info("MT5 desconectado. Bot finalizado.")


    def stop(self):
        """Para o bot"""
        self.running = False
        logger.info("Solicitação de parada do bot recebida")


if __name__ == "__main__":
    # Exemplo de uso
    bot = ScalpingBot(
        symbol="BTCUSDc",
        timeframe=mt5.TIMEFRAME_M5,
        confidence_threshold=85,
        volume=0.01
    )

    # Executar bot
    bot.run(interval=60)  # Verificar a cada 60 segundos
