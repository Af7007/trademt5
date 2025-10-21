"""
Rotas de emergência para hedge
"""

from flask import Blueprint, request, jsonify
import MetaTrader5 as mt5
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

hedge_emergency_bp = Blueprint('hedge_emergency', __name__)


@hedge_emergency_bp.route('/hedge/force', methods=['POST'])
def force_hedge():
    """
    Força abertura de posição oposta para hedge de emergência
    """
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol', 'XAUUSDc')
        magic_number = data.get('magic_number')
        lot_size = data.get('lot_size', 0.01)
        
        if not magic_number:
            return jsonify({
                'success': False,
                'error': 'magic_number obrigatório'
            }), 400
        
        # Conectar MT5
        if not mt5.initialize():
            return jsonify({
                'success': False,
                'error': 'Falha ao conectar MT5'
            }), 500
        
        # Verificar posições
        all_positions = mt5.positions_get(symbol=symbol)
        my_positions = [p for p in all_positions if p.magic == magic_number] if all_positions else []
        
        buy_positions = [p for p in my_positions if p.type == 0]
        sell_positions = [p for p in my_positions if p.type == 1]
        
        logger.info(f"Hedge forçado: BUY={len(buy_positions)}, SELL={len(sell_positions)}")
        
        # Determinar qual posição abrir
        if len(buy_positions) > len(sell_positions):
            # Tem mais BUY, abrir SELL
            signal = 'SELL'
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        elif len(sell_positions) > len(buy_positions):
            # Tem mais SELL, abrir BUY
            signal = 'BUY'
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        else:
            return jsonify({
                'success': False,
                'message': 'Posições já estão balanceadas',
                'buy': len(buy_positions),
                'sell': len(sell_positions)
            })
        
        # Criar ordem
        request_order = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": magic_number,
            "comment": "Hedge Emergência",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Enviar ordem
        result = mt5.order_send(request_order)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✓ Hedge forçado: {signal} @ {price}")
            return jsonify({
                'success': True,
                'message': f'Hedge {signal} executado com sucesso',
                'ticket': result.order,
                'price': result.price,
                'signal': signal,
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.error(f"✗ Falha no hedge: {result.comment}")
            return jsonify({
                'success': False,
                'error': result.comment,
                'retcode': result.retcode
            }), 500
        
    except Exception as e:
        logger.error(f"Erro no hedge forçado: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hedge_emergency_bp.route('/hedge/status', methods=['GET'])
def hedge_status():
    """
    Verifica status de hedge de todas as posições
    """
    try:
        symbol = request.args.get('symbol', 'XAUUSDc')
        
        if not mt5.initialize():
            return jsonify({
                'success': False,
                'error': 'Falha ao conectar MT5'
            }), 500
        
        # Pegar todas as posições
        all_positions = mt5.positions_get(symbol=symbol)
        
        if not all_positions:
            return jsonify({
                'success': True,
                'balanced': True,
                'buy_count': 0,
                'sell_count': 0,
                'message': 'Sem posições abertas'
            })
        
        # Agrupar por magic number
        by_magic = {}
        for p in all_positions:
            if p.magic not in by_magic:
                by_magic[p.magic] = {'buy': 0, 'sell': 0, 'positions': []}
            
            if p.type == 0:
                by_magic[p.magic]['buy'] += 1
            else:
                by_magic[p.magic]['sell'] += 1
            
            by_magic[p.magic]['positions'].append({
                'ticket': p.ticket,
                'type': 'BUY' if p.type == 0 else 'SELL',
                'volume': p.volume,
                'price': p.price_open,
                'profit': p.profit
            })
        
        # Verificar balanceamento
        bots_status = []
        for magic, data in by_magic.items():
            balanced = data['buy'] == data['sell']
            bots_status.append({
                'magic_number': magic,
                'buy_count': data['buy'],
                'sell_count': data['sell'],
                'balanced': balanced,
                'positions': data['positions']
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'bots': bots_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar hedge: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
