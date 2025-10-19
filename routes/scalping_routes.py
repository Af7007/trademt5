from flask import Blueprint, jsonify, request, render_template
import MetaTrader5 as mt5
import threading
import sys
import os

# Adicionar path do app ao sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scalping_bot import ScalpingBot

scalping_bp = Blueprint('scalping', __name__)

# Instância global do bot (será usada a do app.py quando auto-iniciado)
bot_instance = None
bot_thread = None


def get_bot_from_app():
    """
    Tenta obter a instância do bot do app.py se estiver rodando
    """
    try:
        import app
        if hasattr(app, 'scalping_bot_instance') and app.scalping_bot_instance is not None:
            return app.scalping_bot_instance
    except:
        pass
    return bot_instance


@scalping_bp.route('/scalping/dashboard', methods=['GET'])
def scalping_dashboard():
    """
    Render Scalping Bot Dashboard
    """
    return render_template('scalping_dashboard.html')


@scalping_bp.route('/scalping/start', methods=['POST'])
def start_bot():
    """
    Inicia o bot de scalping
    ---
    tags:
      - Scalping Bot
    parameters:
      - name: confidence_threshold
        in: body
        type: integer
        default: 85
        description: Confiança mínima para entrada (%)
      - name: volume
        in: body
        type: number
        default: 0.01
        description: Volume da operação em lotes
      - name: interval
        in: body
        type: integer
        default: 60
        description: Intervalo entre verificações (segundos)
    responses:
      200:
        description: Bot iniciado com sucesso
    """
    global bot_instance, bot_thread

    try:
        # Verificar se bot já está rodando
        if bot_instance and bot_instance.running:
            return jsonify({
                "status": "already_running",
                "message": "Bot já está em execução"
            }), 400

        # Obter parâmetros
        data = request.get_json() or {}
        confidence_threshold = data.get('confidence_threshold', 85)
        volume = data.get('volume', 0.01)
        interval = data.get('interval', 60)
        use_dynamic_risk = data.get('use_dynamic_risk', True)  # Usar risco dinâmico por padrão

        # Criar instância do bot
        bot_instance = ScalpingBot(
            symbol="BTCUSDc",
            timeframe=mt5.TIMEFRAME_M5,
            confidence_threshold=confidence_threshold,
            volume=volume,
            use_dynamic_risk=use_dynamic_risk
        )

        # Iniciar bot em thread separada
        def run_bot():
            bot_instance.run(interval=interval)

        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()

        return jsonify({
            "status": "started",
            "message": "Bot iniciado com sucesso",
            "config": {
                "confidence_threshold": confidence_threshold,
                "volume": volume,
                "interval": interval
            }
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@scalping_bp.route('/scalping/stop', methods=['POST'])
def stop_bot():
    """
    Para o bot de scalping
    ---
    tags:
      - Scalping Bot
    responses:
      200:
        description: Bot parado com sucesso
    """
    global bot_instance

    try:
        if bot_instance is None or not bot_instance.running:
            return jsonify({
                "status": "not_running",
                "message": "Bot não está em execução"
            }), 400

        bot_instance.stop()

        return jsonify({
            "status": "stopped",
            "message": "Bot parado com sucesso"
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@scalping_bp.route('/scalping/status', methods=['GET'])
def get_bot_status():
    """
    Obtém status do bot de scalping
    ---
    tags:
      - Scalping Bot
    responses:
      200:
        description: Status do bot
    """
    try:
        # Tentar obter bot do app.py primeiro, depois da variável local
        current_bot = get_bot_from_app()

        if current_bot is None:
            return jsonify({
                "running": False,
                "message": "Bot não inicializado"
            }), 200

        stats = current_bot.get_stats()

        return jsonify({
            "running": current_bot.running,
            "stats": stats
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@scalping_bp.route('/scalping/execute-once', methods=['POST'])
def execute_once():
    """
    Executa uma verificação única do bot (modo manual)
    ---
    tags:
      - Scalping Bot
    responses:
      200:
        description: Verificação executada
    """
    try:
        # Criar instância temporária
        bot = ScalpingBot(
            symbol="BTCUSDc",
            timeframe=mt5.TIMEFRAME_M5,
            confidence_threshold=85,
            volume=0.01
        )

        result = bot.run_once()

        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@scalping_bp.route('/scalping/positions', methods=['GET'])
def get_active_positions():
    """
    Obtém posições abertas do bot
    ---
    tags:
      - Scalping Bot
    responses:
      200:
        description: Lista de posições abertas
    """
    try:
        if not mt5.initialize():
            return jsonify({"error": "MT5 initialization failed"}), 500

        positions = mt5.positions_get(symbol="BTCUSDc")

        if positions is None:
            return jsonify({
                "symbol": "BTCUSDc",
                "positions": [],
                "count": 0
            }), 200

        positions_list = []
        for pos in positions:
            positions_list.append({
                "ticket": pos.ticket,
                "time": pos.time,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "comment": pos.comment
            })

        return jsonify({
            "symbol": "BTCUSDc",
            "positions": positions_list,
            "count": len(positions_list)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@scalping_bp.route('/scalping/trade-manual', methods=['POST'])
def execute_manual_trade():
    """
    Executa uma operação manual (BUY ou SELL)
    ---
    tags:
      - Scalping Bot
    parameters:
      - name: order_type
        in: body
        type: string
        required: true
        description: Tipo de ordem (BUY ou SELL)
      - name: volume
        in: body
        type: number
        default: 0.01
        description: Volume da operação em lotes
      - name: use_sl_tp
        in: body
        type: boolean
        default: true
        description: Usar Stop Loss e Take Profit automáticos
    responses:
      200:
        description: Ordem executada
    """
    try:
        data = request.get_json() or {}
        order_type_str = data.get('order_type', '').upper()
        volume = float(data.get('volume', 0.01))
        use_sl_tp = data.get('use_sl_tp', True)

        if order_type_str not in ['BUY', 'SELL']:
            return jsonify({
                "status": "error",
                "message": "Tipo de ordem inválido. Use 'BUY' ou 'SELL'"
            }), 400

        # Inicializar MT5
        if not mt5.initialize():
            return jsonify({
                "status": "error",
                "message": "Falha ao inicializar MT5"
            }), 500

        # Obter preço atual
        tick = mt5.symbol_info_tick("BTCUSDc")
        if tick is None:
            return jsonify({
                "status": "error",
                "message": "Falha ao obter preço atual"
            }), 500

        current_price = tick.ask if order_type_str == "BUY" else tick.bid

        # Criar instância temporária do bot para usar funções de cálculo
        from scalping_bot import ScalpingBot
        bot = ScalpingBot(symbol="BTCUSDc", timeframe=mt5.TIMEFRAME_M5)

        # Calcular SL e TP
        sl, tp = 0.0, 0.0
        if use_sl_tp:
            sl, tp = bot.calculate_sl_tp(current_price, order_type_str)

        # Determinar tipo de ordem MT5
        order_type = mt5.ORDER_TYPE_BUY if order_type_str == "BUY" else mt5.ORDER_TYPE_SELL

        # Preparar requisição
        request_dict = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": "BTCUSDc",
            "volume": volume,
            "type": order_type,
            "price": current_price,
            "deviation": 20,
            "magic": 234001,  # Magic number diferente para ordens manuais
            "comment": f"Manual {order_type_str}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Adicionar SL e TP se solicitado
        if use_sl_tp:
            request_dict["sl"] = sl
            request_dict["tp"] = tp

        # Enviar ordem
        result = mt5.order_send(request_dict)

        if result is None:
            return jsonify({
                "status": "error",
                "message": "Falha ao enviar ordem - resultado None"
            }), 500

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({
                "status": "error",
                "message": f"Ordem falhou: {result.retcode} - {result.comment}"
            }), 500

        # Ordem executada com sucesso
        response_data = {
            "status": "success",
            "message": f"Ordem {order_type_str} executada com sucesso!",
            "order": {
                "ticket": result.order,
                "type": order_type_str,
                "volume": result.volume,
                "price": result.price,
                "sl": sl if use_sl_tp else None,
                "tp": tp if use_sl_tp else None
            }
        }

        return jsonify(response_data), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@scalping_bp.route('/scalping/close-position', methods=['POST'])
def close_position():
    """
    Fecha uma posição específica
    ---
    tags:
      - Scalping Bot
    parameters:
      - name: ticket
        in: body
        type: integer
        required: true
        description: Ticket da posição a ser fechada
    responses:
      200:
        description: Posição fechada
    """
    try:
        data = request.get_json() or {}
        ticket = data.get('ticket')

        if not ticket:
            return jsonify({
                "status": "error",
                "message": "Ticket da posição é obrigatório"
            }), 400

        # Inicializar MT5
        if not mt5.initialize():
            return jsonify({
                "status": "error",
                "message": "Falha ao inicializar MT5"
            }), 500

        # Obter informações da posição
        position = mt5.positions_get(ticket=ticket)
        if not position or len(position) == 0:
            return jsonify({
                "status": "error",
                "message": f"Posição {ticket} não encontrada"
            }), 404

        position = position[0]

        # Determinar tipo de ordem para fechar (inverso da posição)
        close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        # Obter preço atual
        tick = mt5.symbol_info_tick(position.symbol)
        if tick is None:
            return jsonify({
                "status": "error",
                "message": "Falha ao obter preço atual"
            }), 500

        close_price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask

        # Preparar requisição de fechamento
        request_dict = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": close_type,
            "position": ticket,
            "price": close_price,
            "deviation": 20,
            "magic": position.magic,
            "comment": "Fechamento manual",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        # Enviar ordem de fechamento
        result = mt5.order_send(request_dict)

        if result is None:
            return jsonify({
                "status": "error",
                "message": "Falha ao fechar posição - resultado None"
            }), 500

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({
                "status": "error",
                "message": f"Falha ao fechar: {result.retcode} - {result.comment}"
            }), 500

        return jsonify({
            "status": "success",
            "message": f"Posição {ticket} fechada com sucesso!",
            "profit": position.profit
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@scalping_bp.route('/scalping/history', methods=['GET'])
def get_today_history():
    """
    Obtém histórico de transações do dia
    ---
    tags:
      - Scalping Bot
    responses:
      200:
        description: Histórico de transações do dia
    """
    try:
        if not mt5.initialize():
            return jsonify({"error": "MT5 initialization failed"}), 500

        # Obter data de hoje (início do dia)
        from datetime import datetime, time
        today = datetime.combine(datetime.today(), time.min)

        # Obter deals do dia para BTCUSDc
        deals = mt5.history_deals_get(today, datetime.now(), symbol="BTCUSDc")

        if deals is None:
            return jsonify({
                "symbol": "BTCUSDc",
                "deals": [],
                "count": 0,
                "total_profit": 0.0
            }), 200

        deals_list = []
        total_profit = 0.0

        for deal in deals:
            # Filtrar apenas deals de entrada e saída (não comissões)
            if deal.entry == mt5.DEAL_ENTRY_IN or deal.entry == mt5.DEAL_ENTRY_OUT:
                deal_info = {
                    "ticket": deal.ticket,
                    "order": deal.order,
                    "time": deal.time,
                    "type": "BUY" if deal.type == mt5.DEAL_TYPE_BUY else "SELL",
                    "entry": "IN" if deal.entry == mt5.DEAL_ENTRY_IN else "OUT",
                    "volume": deal.volume,
                    "price": deal.price,
                    "profit": deal.profit,
                    "comment": deal.comment
                }
                deals_list.append(deal_info)
                total_profit += deal.profit

        return jsonify({
            "symbol": "BTCUSDc",
            "deals": deals_list,
            "count": len(deals_list),
            "total_profit": round(total_profit, 2)
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
