"""
Gerenciador de Hedge - Monitora e ajusta posições em hedge
"""

import MetaTrader5 as mt5
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HedgeManager:
    """Gerencia posições em hedge para maximizar lucro"""
    
    @staticmethod
    def check_and_close_losing_position(symbol, magic_number):
        """
        Verifica se uma posição em hedge bateu TP e fecha a perdedora
        
        Args:
            symbol: Símbolo da posição
            magic_number: Magic number do bot
            
        Returns:
            bool: True se fechou alguma posição
        """
        try:
            # Pegar posições do bot
            all_positions = mt5.positions_get(symbol=symbol)
            if not all_positions:
                return False
            
            my_positions = [p for p in all_positions if p.magic == magic_number]
            if len(my_positions) < 2:
                return False
            
            buy_positions = [p for p in my_positions if p.type == 0]
            sell_positions = [p for p in my_positions if p.type == 1]
            
            # Verificar se tem hedge ativo
            if not (buy_positions and sell_positions):
                return False
            
            # Calcular lucro de cada lado
            buy_profit = sum(p.profit for p in buy_positions)
            sell_profit = sum(p.profit for p in sell_positions)
            total_profit = buy_profit + sell_profit
            
            logger.info(f"Hedge Status: BUY P&L=${buy_profit:.2f}, SELL P&L=${sell_profit:.2f}, Total=${total_profit:.2f}")
            
            # Se uma posição está em lucro significativo e a outra em prejuízo
            # Fechar a perdedora para garantir lucro líquido
            
            # BUY lucrando, SELL perdendo
            if buy_profit > 5 and sell_profit < -2:
                logger.info(f"🎯 BUY lucrando ${buy_profit:.2f}, SELL perdendo ${sell_profit:.2f}")
                
                # Se lucro líquido é positivo, fechar SELL perdedora
                if total_profit > 2:
                    logger.info(f"✓ Lucro líquido ${total_profit:.2f} - Fechando SELL perdedora")
                    for pos in sell_positions:
                        HedgeManager._close_position(pos)
                    return True
            
            # SELL lucrando, BUY perdendo
            elif sell_profit > 5 and buy_profit < -2:
                logger.info(f"🎯 SELL lucrando ${sell_profit:.2f}, BUY perdendo ${buy_profit:.2f}")
                
                # Se lucro líquido é positivo, fechar BUY perdedora
                if total_profit > 2:
                    logger.info(f"✓ Lucro líquido ${total_profit:.2f} - Fechando BUY perdedora")
                    for pos in buy_positions:
                        HedgeManager._close_position(pos)
                    return True
            
            # Ambas lucrando - deixar correr
            elif buy_profit > 0 and sell_profit > 0:
                logger.info(f"✓ Ambas lucrando - Mantendo hedge")
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao verificar hedge: {e}")
            return False
    
    @staticmethod
    def _close_position(position):
        """Fecha uma posição específica"""
        try:
            symbol = position.symbol
            ticket = position.ticket
            volume = position.volume
            pos_type = "BUY" if position.type == 0 else "SELL"
            
            # Determinar tipo de fechamento
            if position.type == 0:  # BUY
                close_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid
            else:  # SELL
                close_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask
            
            # Criar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": position.magic,
                "comment": "Hedge Manager - Fechar perdedora",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar ordem
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✓ Posição {pos_type} fechada! Ticket: {ticket}, P&L: ${position.profit:.2f}")
                return True
            else:
                logger.error(f"✗ Falha ao fechar {pos_type}: {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao fechar posição: {e}")
            return False


# Instância global
hedge_manager = HedgeManager()
