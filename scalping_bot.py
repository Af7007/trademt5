"""
Bot de Scalping - Implementação básica
Logica simples de scalping baseada em indicadores técnicos
"""

import MetaTrader5 as mt5
import time
import threading
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ScalpingBot:
    """
    Bot de Scalping Básico
    Mantém posições por curtos períodos de tempo visando pequenos lucros
    """

    def __init__(self, symbol="BTCUSDc", timeframe=mt5.TIMEFRAME_M5,
                 confidence_threshold=85, volume=0.01, use_dynamic_risk=True):
        self.symbol = symbol
        self.timeframe = timeframe
        self.confidence_threshold = confidence_threshold
        self.volume = volume
        self.use_dynamic_risk = use_dynamic_risk

        self.running = False
        self.position_active = False
        self.last_signal_time = None

        # Estatísticas do bot
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'current_streak': 0,
            'best_streak': 0
        }

        logger.info(f"ScalpingBot inicializado: {symbol} {timeframe} threshold={confidence_threshold}% volume={volume}")

    def calculate_sl_tp(self, price, order_type):
        """
        Calcula Stop Loss e Take Profit
        SL = 0.5x TP (mais conservador para scalping)
        """
        if order_type == "BUY":
            tp = price + 0.50  # $0.50 TP
            sl = price - 0.25  # $0.25 SL
        else:  # SELL
            tp = price - 0.50  # $0.50 TP
            sl = price + 0.25  # $0.25 SL

        logger.info(f"Calculado SL/TP: {order_type} Price=${price:.2f} SL=${sl:.2f} TP=${tp:.2f}")
        return sl, tp

    def run_once(self):
        """
        Executa uma verificação única (teste)
        """
        try:
            if not mt5.initialize():
                return {"error": "MT5 não inicializado"}

            # Obter dados atuais
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                return {"error": "Falha ao obter dados do símbolo"}

            # Simulação de análise
            current_price = tick.ask if tick.ask > 0 else tick.bid

            # Análise básico (sempre HOLD para teste seguro)
            analysis = {
                'confidence': 0.0,  # Sempre 0 para não executar trades reais
                'signal': 'HOLD',
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'reason': 'Modo teste seguro - sempre HOLD'
            }

            logger.info(f"Análise executada: {analysis['signal']} conf={analysis['confidence']}")
            return analysis

        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return {"error": str(e)}

    def run(self, interval=60):
        """
        Executa o loop principal do bot
        """
        self.running = True
        logger.info(f"ScalpingBot iniciado com intervalo de {interval} segundos")

        while self.running:
            try:
                # Executar verificação
                result = self.run_once()

                if 'error' in result:
                    logger.warning(f"Erro na verificação: {result['error']}")

                # Aguardar próximo ciclo
                time.sleep(interval)

            except Exception as e:
                logger.error(f"Erro no loop principal: {e}")
                time.sleep(interval * 2)  # Aguardar mais em caso de erro

        logger.info("ScalpingBot parado")

    def stop(self):
        """
        Para o bot
        """
        logger.info("Parando ScalpingBot...")
        self.running = False

    def get_stats(self):
        """
        Retorna estatísticas do bot
        """
        return {
            'symbol': self.symbol,
            'running': self.running,
            'position_active': self.position_active,
            'confidence_threshold': self.confidence_threshold,
            'volume': self.volume,
            'stats': self.stats,
            'last_update': datetime.now().isoformat()
        }
