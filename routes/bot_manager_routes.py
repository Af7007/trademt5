"""
Rotas para gerenciamento de múltiplos bots
"""
from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

from services.bot_manager_service import bot_manager

bot_manager_bp = Blueprint('bot_manager', __name__)
logger = logging.getLogger(__name__)


@bot_manager_bp.route('/bots', methods=['GET'])
def get_all_bots():
    """
    Lista todos os bots
    """
    try:
        bots = bot_manager.get_all_bots()
        return jsonify({
            'success': True,
            'bots': bots,
            'total': len(bots),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/active', methods=['GET'])
def get_active_bots():
    """
    Lista apenas bots ativos
    """
    try:
        bots = bot_manager.get_active_bots()
        return jsonify({
            'success': True,
            'bots': bots,
            'total': len(bots),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/create', methods=['POST'])
def create_bot():
    """
    Cria um novo bot
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Configuração obrigatória',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Aceitar tanto {config: {...}} quanto {...} diretamente
        if 'config' in data:
            config = data['config']
        else:
            config = data
        
        # Validar campos obrigatórios
        required_fields = ['symbol']
        for field in required_fields:
            if field not in config:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        # Criar bot
        bot_id = bot_manager.create_bot(config)
        
        # Iniciar bot automaticamente
        started = bot_manager.start_bot(bot_id)
        
        return jsonify({
            'success': True,
            'bot_id': bot_id,
            'started': started,
            'message': f'Bot criado e {"iniciado" if started else "aguardando início"}',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar bot: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/<bot_id>', methods=['GET'])
def get_bot(bot_id):
    """
    Obtém detalhes de um bot específico
    """
    try:
        bot = bot_manager.get_bot(bot_id)
        
        if not bot:
            return jsonify({
                'success': False,
                'error': 'Bot não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        return jsonify({
            'success': True,
            'bot': bot.get_status(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/<bot_id>/start', methods=['POST'])
def start_bot(bot_id):
    """
    Inicia um bot específico
    """
    try:
        success = bot_manager.start_bot(bot_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Bot {bot_id} iniciado',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha ao iniciar bot',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/<bot_id>/stop', methods=['POST'])
def stop_bot(bot_id):
    """
    Para um bot específico
    """
    try:
        success = bot_manager.stop_bot(bot_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Bot {bot_id} parado',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha ao parar bot',
                'timestamp': datetime.now().isoformat()
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/<bot_id>/delete', methods=['DELETE'])
def delete_bot(bot_id):
    """
    Remove um bot
    """
    try:
        success = bot_manager.delete_bot(bot_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Bot {bot_id} removido',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Bot não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/<bot_id>/close-position/<int:ticket>', methods=['POST'])
def close_position(bot_id, ticket):
    """
    Fecha uma posição específica
    """
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            return jsonify({
                'success': False,
                'error': 'Falha ao conectar com MT5'
            }), 500
        
        # Buscar a posição
        position = mt5.positions_get(ticket=ticket)
        
        if not position or len(position) == 0:
            return jsonify({
                'success': False,
                'error': f'Posição #{ticket} não encontrada'
            }), 404
        
        pos = position[0]
        
        # Determinar tipo de ordem para fechar
        if pos.type == 0:  # BUY
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(pos.symbol).bid
        else:  # SELL
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).ask
        
        # Criar request de fechamento
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 10,
            "magic": pos.magic,
            "comment": f"Close by Bot Manager",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Enviar ordem
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Posição #{ticket} fechada com sucesso")
            return jsonify({
                'success': True,
                'message': f'Posição #{ticket} fechada',
                'profit': pos.profit
            })
        else:
            logger.error(f"Erro ao fechar posição #{ticket}: {result.comment}")
            return jsonify({
                'success': False,
                'error': f'Erro ao fechar: {result.comment}'
            }), 400
            
    except Exception as e:
        logger.error(f"Erro ao fechar posição: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bot_manager_bp.route('/bots/retrain-mlp', methods=['POST'])
def retrain_mlp():
    """
    Retreina o modelo MLP
    """
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol', 'BTCUSDc')
        timeframe = data.get('timeframe', 'M1')
        num_samples = data.get('num_samples', 500)
        
        from services.mlp_predictor import mlp_predictor
        
        logger.info(f"Retreinando MLP: {symbol} {timeframe} ({num_samples} amostras)")
        
        # Retreinar em thread para não bloquear
        import threading
        
        result = {'success': False, 'message': ''}
        
        def train():
            success = mlp_predictor.auto_train_from_mt5(symbol, timeframe, num_samples)
            result['success'] = success
            result['message'] = 'Modelo retreinado com sucesso!' if success else 'Falha ao retreinar modelo'
        
        train_thread = threading.Thread(target=train)
        train_thread.start()
        train_thread.join(timeout=60)  # Aguardar até 60 segundos
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao retreinar MLP: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@bot_manager_bp.route('/bots/emergency-stop-all', methods=['POST'])
def emergency_stop_all():
    """
    Para todos os bots em emergência
    """
    try:
        results = bot_manager.emergency_stop_all()
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f'{len(results)} bots processados',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
