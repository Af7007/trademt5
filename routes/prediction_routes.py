"""
Rotas da API para o módulo de predição de trading
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from prediction import PredictionEngine, PredictionRequest

logger = logging.getLogger(__name__)

prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')

# Instância global do motor de predição
prediction_engine = PredictionEngine()


@prediction_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check do módulo de predição
    ---
    tags:
      - Prediction
    responses:
      200:
        description: Módulo funcionando
    """
    return jsonify({
        'status': 'healthy',
        'module': 'prediction',
        'timestamp': datetime.now().isoformat()
    })


@prediction_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    Gera predição completa baseada nos parâmetros
    ---
    tags:
      - Prediction
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - symbol
            - target_profit
            - balance
          properties:
            symbol:
              type: string
              example: "XAUUSDc"
              description: Símbolo para análise
            target_profit:
              type: number
              example: 30.0
              description: Lucro alvo em USD
            balance:
              type: number
              example: 1000.0
              description: Banca disponível em USD
            timeframe:
              type: string
              example: "M1"
              description: Timeframe desejado (M1, M5, M15, H1, H4, D1)
            lot_size:
              type: number
              example: 0.01
              description: Tamanho do lote (opcional, será calculado se não fornecido)
            take_profit:
              type: number
              example: 100
              description: Take profit em pontos (opcional)
            stop_loss:
              type: number
              example: 50
              description: Stop loss em pontos (opcional)
            max_operations:
              type: integer
              example: 10
              description: Limite de operações (opcional)
            risk_percentage:
              type: number
              example: 2.0
              description: Percentual de risco por operação
    responses:
      200:
        description: Predição gerada com sucesso
        schema:
          type: object
          properties:
            success:
              type: boolean
            result:
              type: object
            timestamp:
              type: string
      400:
        description: Parâmetros inválidos
      500:
        description: Erro interno
    """
    try:
        data = request.get_json()
        
        # Validar parâmetros obrigatórios
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        required_fields = ['symbol', 'target_profit', 'balance']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Campos obrigatórios faltando: {", ".join(missing_fields)}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Criar requisição de predição
        pred_request = PredictionRequest(
            symbol=data['symbol'],
            target_profit=float(data['target_profit']),
            balance=float(data['balance']),
            timeframe=data.get('timeframe', 'M1'),
            lot_size=float(data['lot_size']) if data.get('lot_size') else None,
            take_profit=float(data['take_profit']) if data.get('take_profit') else None,
            stop_loss=float(data['stop_loss']) if data.get('stop_loss') else None,
            max_operations=int(data['max_operations']) if data.get('max_operations') else None,
            risk_percentage=float(data.get('risk_percentage', 2.0))
        )
        
        # Gerar predição
        logger.info(f"Gerando predição para {pred_request.symbol}")
        result = prediction_engine.predict(pred_request)
        
        return jsonify({
            'success': True,
            'result': result.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 400
    except Exception as e:
        logger.error(f"Erro ao gerar predição: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@prediction_bp.route('/market-analysis/<symbol>', methods=['GET'])
def get_market_analysis(symbol: str):
    """
    Obtém análise de mercado para um símbolo
    ---
    tags:
      - Prediction
    parameters:
      - name: symbol
        in: path
        type: string
        required: true
        description: Símbolo para análise (ex: XAUUSDc)
      - name: timeframe
        in: query
        type: string
        default: M1
        description: Timeframe (M1, M5, M15, H1, H4, D1)
    responses:
      200:
        description: Análise de mercado
      404:
        description: Símbolo não encontrado
      500:
        description: Erro interno
    """
    try:
        timeframe = request.args.get('timeframe', 'M1')
        
        # Criar requisição mínima para análise
        pred_request = PredictionRequest(
            symbol=symbol,
            target_profit=100.0,  # Valor dummy
            balance=1000.0,  # Valor dummy
            timeframe=timeframe
        )
        
        # Analisar mercado
        market_analysis = prediction_engine._analyze_market(pred_request)
        
        return jsonify({
            'success': True,
            'analysis': market_analysis.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
    except ValueError as e:
        logger.error(f"Símbolo não encontrado: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 404
    except Exception as e:
        logger.error(f"Erro ao analisar mercado: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@prediction_bp.route('/symbol-info/<symbol>', methods=['GET'])
def get_symbol_info(symbol: str):
    """
    Obtém informações detalhadas de um símbolo
    ---
    tags:
      - Prediction
    parameters:
      - name: symbol
        in: path
        type: string
        required: true
        description: Símbolo (ex: XAUUSDc)
    responses:
      200:
        description: Informações do símbolo
      404:
        description: Símbolo não encontrado
    """
    try:
        symbol_info = prediction_engine.data_collector.get_symbol_info(symbol)
        
        if not symbol_info:
            return jsonify({
                'success': False,
                'error': f'Símbolo {symbol} não encontrado',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        return jsonify({
            'success': True,
            'symbol_info': symbol_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter informações do símbolo: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@prediction_bp.route('/quick-prediction', methods=['POST'])
def quick_prediction():
    """
    Predição rápida com parâmetros mínimos
    ---
    tags:
      - Prediction
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - symbol
            - target_profit
          properties:
            symbol:
              type: string
              example: "XAUUSDc"
            target_profit:
              type: number
              example: 30.0
            balance:
              type: number
              example: 1000.0
              default: 1000.0
    responses:
      200:
        description: Predição rápida gerada
    """
    try:
        data = request.get_json()
        
        if not data or 'symbol' not in data or 'target_profit' not in data:
            return jsonify({
                'success': False,
                'error': 'Campos obrigatórios: symbol, target_profit',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Criar requisição com valores padrão
        pred_request = PredictionRequest(
            symbol=data['symbol'],
            target_profit=float(data['target_profit']),
            balance=float(data.get('balance', 1000.0)),
            timeframe='M1',
            risk_percentage=2.0
        )
        
        # Gerar predição
        result = prediction_engine.predict(pred_request)
        
        # Retornar apenas informações resumidas
        summary = {
            'symbol': result.request.symbol,
            'target_profit': result.request.target_profit,
            'estimated_operations': result.estimated_operations,
            'estimated_duration': result.estimated_duration_description,
            'success_probability': f"{result.success_probability * 100:.1f}%",
            'best_timeframe': result.best_timeframe,
            'risk_level': result.risk_level,
            'recommended_lot_size': result.recommended_trades[0].lot_size if result.recommended_trades else 0.01,
            'warnings': result.warnings,
            'top_recommendation': result.recommendations[0] if result.recommendations else None
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'full_result': result.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro na predição rápida: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@prediction_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Interface web para visualização das predições"""
    return render_template('prediction_dashboard.html')


@prediction_bp.route('/examples', methods=['GET'])
def get_examples():
    """
    Retorna exemplos de requisições
    ---
    tags:
      - Prediction
    responses:
      200:
        description: Exemplos de uso
    """
    examples = {
        'example_1': {
            'description': 'Predição básica para XAUUSDc',
            'request': {
                'symbol': 'XAUUSDc',
                'target_profit': 30.0,
                'balance': 1000.0,
                'timeframe': 'M1'
            }
        },
        'example_2': {
            'description': 'Predição com parâmetros customizados',
            'request': {
                'symbol': 'XAUUSDc',
                'target_profit': 50.0,
                'balance': 2000.0,
                'timeframe': 'M5',
                'lot_size': 0.02,
                'take_profit': 150,
                'stop_loss': 75,
                'max_operations': 20,
                'risk_percentage': 1.5
            }
        },
        'example_3': {
            'description': 'Predição para BTCUSDc',
            'request': {
                'symbol': 'BTCUSDc',
                'target_profit': 100.0,
                'balance': 5000.0,
                'timeframe': 'H1'
            }
        }
    }
    
    return jsonify({
        'examples': examples,
        'endpoint': '/prediction/analyze',
        'method': 'POST',
        'timestamp': datetime.now().isoformat()
    })
