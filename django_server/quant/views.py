"""
Views do Django para o sistema MLP Trading - Versão local
"""

import json
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Views básicas do Trading MLP
def mlp_dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard principal MLP"""
    # Dados simulados para demonstrar o dashboard completo
    today_stats = {
        'total_analyses': 156,
        'total_trades': 23,
        'win_rate': 68.5,
        'total_profit': 1247.83,
        'buy_signals': 89,
        'sell_signals': 67,
        'hold_signals': 45
    }

    # Estatísticas mensais simuladas
    monthly_stats = [
        {'date': '19/10', 'total_trades': 23, 'total_profit': 1247.83, 'buy_signals': 14, 'sell_signals': 9},
        {'date': '18/10', 'total_trades': 31, 'total_profit': 892.45, 'buy_signals': 18, 'sell_signals': 13},
        {'date': '17/10', 'total_trades': 28, 'total_profit': -345.21, 'buy_signals': 15, 'sell_signals': 13},
        {'date': '16/10', 'total_trades': 35, 'total_profit': 2156.78, 'buy_signals': 21, 'sell_signals': 14},
    ]

    # Análises recentes simuladas
    recent_analyses = [
        {
            'id': 158, 'symbol': 'BTCUSDc', 'signal': 'BUY', 'confidence': 87.5,
            'timestamp': datetime.now() - timedelta(minutes=2),
            'rsi': 42.3, 'macd_signal': -0.0012, 'bb_upper': 65800, 'bb_lower': 64200
        },
        {
            'id': 157, 'symbol': 'BTCUSDc', 'signal': 'SELL', 'confidence': 73.2,
            'timestamp': datetime.now() - timedelta(minutes=5),
            'rsi': 68.7, 'macd_signal': 0.0021, 'bb_upper': 65200, 'bb_lower': 64800
        },
        {
            'id': 156, 'symbol': 'BTCUSDc', 'signal': 'HOLD', 'confidence': 52.1,
            'timestamp': datetime.now() - timedelta(minutes=8),
            'rsi': 55.4, 'macd_signal': -0.0005, 'bb_upper': 65000, 'bb_lower': 64700
        },
        {
            'id': 155, 'symbol': 'EURUSD', 'signal': 'BUY', 'confidence': 91.8,
            'timestamp': datetime.now() - timedelta(minutes=12),
            'rsi': 38.9, 'macd_signal': -0.0008, 'bb_upper': 1.0850, 'bb_lower': 1.0780
        },
    ]

    context = {
        'title': 'MLP Dashboard - Sistema Operacional',
        'current_time': datetime.now(),
        'last_update': datetime.now(),

        # Dados principais
        'today_stats': today_stats,
        'monthly_stats': monthly_stats,
        'recent_analyses': recent_analyses,

        # Configurações do sistema
        'bot_config': {
            'is_running': True,
            'confidence_threshold': 0.85,
            'take_profit': 0.50,
            'auto_trading_enabled': True,
            'max_daily_trades': 50
        },

        # Status dos serviços
        'system_status': {
            'django_online': True,
            'flask_online': True,
            'mt5_connected': True,
            'database_ok': True
        }
    }
    return render(request, 'quant/mlp_dashboard.html', context)

def mlp_analyses(request: HttpRequest) -> HttpResponse:
    """Página de análises"""
    # Dados simulados de análises completos
    analyses_simulated = []  # Usar variável local para evitar conflito

    import random
    for i in range(15):  # 15 análises para demonstração
        analysis_data = {
            'id': 200 + i + 1,
            'symbol': random.choice(['BTCUSDc', 'EURUSD', 'GBPUSD', 'USDJPY']),
            'signal': random.choice(['BUY', 'SELL', 'HOLD']),
            'confidence': round(random.uniform(65, 95), 1),
            'timestamp': datetime.now() - timedelta(minutes=random.randint(1, 180)),
            'rsi': round(random.uniform(25, 75), 1),
            'macd_signal': round(random.uniform(-0.002, 0.002), 4),
            'bb_upper': 0,
            'bb_lower': 0
        }

        # Define valores de Bollinger Bands baseados no símbolo
        if analysis_data['symbol'] == 'BTCUSDc':
            analysis_data['bb_upper'] = round(random.uniform(64500, 66500), 0)
            analysis_data['bb_lower'] = analysis_data['bb_upper'] - 1500
        else:
            analysis_data['bb_upper'] = round(random.uniform(1.0800, 1.0950), 4)
            analysis_data['bb_lower'] = round(random.uniform(1.0750, 1.0850), 4)

        analyses_simulated.append(analysis_data)

    # Ordenar por mais recente
    analyses_simulated.sort(key=lambda x: x['timestamp'], reverse=True)

    context = {
        'title': 'MLP Análises - Histórico Completo',
        'current_time': datetime.now(),
        'recent_analyses': analyses_simulated,  # Usar a variável local
        'current_time_iso': datetime.now().isoformat(),
        'analysis_count': len(analyses_simulated)
    }
    return render(request, 'quant/mlp_analyses.html', context)

def mlp_trades(request: HttpRequest) -> HttpResponse:
    """Página de trades"""
    # Dados de estatísticas simuladas
    trades_stats = {
        'total_trades': 142,
        'winning_trades': 96,
        'win_rate': 67.6,
        'total_profit': 24567.83,
        'avg_profit': 173.01
    }

    # Análise dos dados por período
    best_trade = "$245.67"
    worst_trade = "-$89.23"
    max_drawdown = "5.2%"
    sharpe_ratio = "1.45"

    # Dados de trades simulados
    trades_data = []
    symbols = ['BTCUSDc', 'EURUSD', 'GBPUSD', 'USDJPY']
    statuses = ['OPEN', 'CLOSED_PROFIT', 'CLOSED_LOSS']
    types = ['BUY', 'SELL']

    import random
    for i in range(25):  # 25 trades para demonstração
        symbol = random.choice(symbols)
        trade_type = random.choice(types)
        status = random.choice(statuses)
        volume = round(random.uniform(0.1, 2.0), 2)

        if symbol == 'BTCUSDc':
            entry_price = round(random.uniform(63000, 67000), 2)
            exit_price = round(random.uniform(62000, 68000), 2) if status.startswith('CLOSED') else None
        else:
            entry_price = round(random.uniform(1.05, 1.15), 4)
            exit_price = round(random.uniform(1.03, 1.17), 4) if status.startswith('CLOSED') else None

        profit = None
        if exit_price:
            if trade_type == 'BUY':
                profit = round(((exit_price - entry_price) * 10000) / 10, 2)  # Mini lot calculation
            else:
                profit = round(((entry_price - exit_price) * 10000) / 10, 2)

        trade = {
            'ticket': str(random.randint(21800000, 22100000)),
            'symbol': symbol,
            'type': trade_type,
            'volume': volume,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'profit': profit,
            'status': status,
            'entry_time': datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23)),
            'exit_time': datetime.now() - timedelta(days=random.randint(0, 5), minutes=random.randint(1, 1440)) if status.startswith('CLOSED') else None
        }
        trades_data.append(trade)

    # Ordenar por data mais recente
    trades_data.sort(key=lambda x: x['entry_time'], reverse=True)

    context = {
        'title': 'MLP Trades - Histórico Completo',
        'current_time': datetime.now(),
        'trades_stats': trades_stats,
        'trades_data': trades_data,
        'best_trade': best_trade,
        'worst_trade': worst_trade,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio
    }
    return render(request, 'quant/mlp_trades.html', context)

def mlp_control(request: HttpRequest) -> HttpResponse:
    """Página de controle MLP"""
    context = {
        'title': 'MLP Control Center',
        'current_time': datetime.now(),
        'status': 'operational',
        'crypto_tokens': [
            {'symbol': 'BTCUSDc', 'price': 'N/A'},
            {'symbol': 'EURUSD', 'price': 'N/A'},
            {'symbol': 'GBPUSD', 'price': 'N/A'},
        ],
        'current_analysis': None,
        'json_storage': 'available',
        'trade_count': 0,
        'last_update': datetime.now(),
    }
    return render(request, 'quant/mlp_control.html', context)

# API endpoints com CSRF exempt
@csrf_exempt
def mlp_analyze(request: HttpRequest) -> JsonResponse:
    """Analisa mercado via MLP"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        import random
        import MetaTrader5 as mt5

        # Conectar ao MT5 se não estiver conectado
        if not mt5.initialize():
            logger.warning("MT5 não conectado - usando dados simulados")
            mt5_connected = False
        else:
            mt5_connected = True

        signals = ['BUY', 'SELL', 'HOLD']
        signal = random.choice(signals)

        # Dados de preço reais do MT5
        price_data = {
            'open': 0,
            'high': 0,
            'low': 0,
            'close': 0,
            'volume': 0
        }

        if mt5_connected:
            try:
                # Buscar última barra do timeframe atual
                symbol = 'BTCUSDc'
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)

                if rates and len(rates) > 0:
                    rate = rates[0]
                    price_data = {
                        'open': float(rate['open']),
                        'high': float(rate['high']),
                        'low': float(rate['low']),
                        'close': float(rate['close']),
                        'volume': int(rate['tick_volume']),
                        'spread': int(rate['spread']),
                        'timestamp': datetime.fromtimestamp(rate['time']).isoformat()
                    }
                    logger.info(f"Dados MT5 obtidos: {price_data}")
                else:
                    logger.warning("Não foi possível obter dados MT5, usando simulação")
                    mt5_connected = False

            except Exception as mt5_error:
                logger.error(f"Erro ao obter dados MT5: {mt5_error}")
                mt5_connected = False

        # Se não conseguiu dados MT5, usar dados simulados baseados no BTC real
        if not mt5_connected or price_data['open'] == 0:
            # Valores aproximados do BTC real para demonstração
            base_btc = 66400  # Aproximado valor real do BTC
            variation = random.uniform(-0.02, 0.02)  # +/- 2%
            close = base_btc * (1 + variation)

            price_data = {
                'open': round(close * random.uniform(0.998, 1.002), 2),
                'high': round(close * random.uniform(1.001, 1.015), 2),
                'low': round(close * random.uniform(0.985, 0.999), 2),
                'close': round(close, 2),
                'volume': random.randint(500000, 2000000),
                'timestamp': datetime.now().isoformat(),
                'source': 'SIMULATED (MT5 not available)'
            }
            logger.info("Usando dados simulados devido a desconexão MT5")

        result = {
            'success': True,
            'signal': signal,
            'confidence': round(random.uniform(0.6, 0.95), 2),
            'analysis_id': random.randint(1000, 9999),
            'timestamp': datetime.now().isoformat(),
            'symbol': 'BTCUSDc',
            'mt5_connected': mt5_connected,
            'indicators': {
                'rsi': round(random.uniform(30, 70), 1),
                'macd': round(random.uniform(-0.01, 0.01), 6),  # Valores mais realistas para MACD
                'bb_upper': round(random.uniform(1.08, 1.12), 2),
                'bb_middle': round(random.uniform(1.00, 1.05), 2),  # Média Móvel 20
                'bb_lower': round(random.uniform(0.98, 1.02), 2),
            },
            'price_data': price_data
        }

        logger.info(f"MLP Analysis executed: {result}")
        return JsonResponse(result)

    except Exception as e:
        logger.error(f"MLP analysis error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def mlp_execute(request: HttpRequest) -> JsonResponse:
    """Executa sinal de trading"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body) if request.body else request.POST
        signal = data.get('signal')
        symbol = data.get('symbol', 'BTCUSDc')

        if signal not in ['BUY', 'SELL']:
            return JsonResponse({
                'success': False,
                'error': 'Invalid signal. Use BUY or SELL'
            }, status=400)

        # Simulação de execução de trade
        import random
        price = round(random.uniform(60000, 65000), 2)
        volume = round(random.uniform(0.01, 0.1), 3)
        ticket = random.randint(12345678, 87654321)

        result = {
            'success': True,
            'trade': {
                'ticket': str(ticket),
                'symbol': symbol,
                'type': signal,
                'entry_price': price,
                'volume': volume,
                'executed_at': datetime.now().isoformat(),
                'status': 'OPEN'
            },
            'message': f"Trade {signal} executed at ${price}"
        }

        logger.info(f"MLP Trade executed: {result}")
        return JsonResponse(result)

    except Exception as e:
        logger.error(f"MLP execute error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def mlp_bot_auto_start(request: HttpRequest) -> JsonResponse:
    """Inicia bot automático via thread"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        from .mlp_bot import mlp_bot

        # Verifica se bot já está rodando
        status = mlp_bot.get_status()
        if status['is_running']:
            return JsonResponse({
                'success': False,
                'error': 'Bot já está rodando',
                'status': status
            })

        # Inicia bot
        if mlp_bot.start():
            return JsonResponse({
                'success': True,
                'message': '✅ BOT AUTOMÁTICO MLP INICIADO!',
                'status': mlp_bot.get_status()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Falha ao iniciar bot automático'
            })

    except Exception as e:
        logger.error(f"Erro ao iniciar bot automático: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def mlp_bot_auto_stop(request: HttpRequest) -> JsonResponse:
    """Para bot automático"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        from .mlp_bot import mlp_bot

        # Verifica se bot está rodando
        status = mlp_bot.get_status()
        if not status['is_running']:
            return JsonResponse({
                'success': False,
                'error': 'Bot não está rodando',
                'status': status
            })

        # Para bot
        if mlp_bot.stop():
            return JsonResponse({
                'success': True,
                'message': '🛑 BOT AUTOMÁTICO MLP PARADO!',
                'status': mlp_bot.get_status()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Falha ao parar bot automático'
            })

    except Exception as e:
        logger.error(f"Erro ao parar bot automático: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def mlp_bot_status(request: HttpRequest) -> JsonResponse:
    """Status do bot automático"""
    try:
        from .mlp_bot import mlp_bot

        status = mlp_bot.get_status()
        config = status['config']

        return JsonResponse({
            'success': True,
            'bot_running': status['is_running'],
            'auto_trading': config.get('auto_trading_enabled', False),
            'confidence_threshold': config.get('confidence_threshold', 0.85),
            'take_profit': config.get('take_profit', 0.50),
            'operation_interval': config.get('operation_interval', 60),
            'last_operation': config.get('last_operation_time'),
            'can_trade_now': status.get('can_trade_now', False),
            'message': f"🤖 Bot {'ATIVO' if status['is_running'] else 'PARADO'} - Threshold: {config.get('confidence_threshold', 0.85)*100:.0f}% - TP: ${config.get('take_profit', 0.50):.2f}"
        })

    except Exception as e:
        logger.error(f"Erro ao obter status do bot: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def mlp_start(request: HttpRequest) -> JsonResponse:
    """Inicia o bot MLP"""
    try:
        # Simulação de start do bot
        logger.info("MLP Bot start requested")
        return JsonResponse({
            'success': True,
            'message': 'MLP Trading Bot iniciado com sucesso',
            'timestamp': datetime.now().isoformat(),
            'bot_status': 'running'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def mlp_stop(request: HttpRequest) -> JsonResponse:
    """Para o bot MLP"""
    try:
        # Simulação de stop do bot
        logger.info("MLP Bot stop requested")
        return JsonResponse({
            'success': True,
            'message': 'MLP Trading Bot parado com sucesso',
            'timestamp': datetime.now().isoformat(),
            'bot_status': 'stopped'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def mlp_health(request: HttpRequest) -> JsonResponse:
    """Status da saúde do sistema MLP"""
    return JsonResponse({
        'status': 'healthy',
        'systems': {
            'django': True,
            'json_storage': True,
            'trading_engine': True,
        },
        'statistics': {
            'analyses_done': random.randint(50, 200),
            'trades_executed': random.randint(5, 30),
            'active_bot': True,
            'profit_today': round(random.uniform(-100, 300), 2)
        },
        'timestamp': datetime.now().isoformat()
    })

def mlp_history(request: HttpRequest) -> JsonResponse:
    """Histórico de análises"""
    import random
    analyses = []
    symbols = ['BTCUSDc', 'EURUSD', 'GBPUSD']

    for i in range(10):
        analysis = {
            'id': random.randint(1000, 9999),
            'symbol': random.choice(symbols),
            'signal': random.choice(['BUY', 'SELL', 'HOLD']),
            'confidence': round(random.uniform(0.5, 0.95), 2),
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat(),
            'rsi': round(random.uniform(30, 70), 1),
            'macd_signal': round(random.uniform(-0.001, 0.001), 4)
        }
        analyses.append(analysis)

    return JsonResponse({
        'success': True,
        'histories': analyses,  # Changed from 'data' to match expectations
        'count': len(analyses)
    })

def mlp_trades_api(request: HttpRequest) -> JsonResponse:
    """Histórico de trades"""
    import random
    trades = []

    for i in range(5):
        trade = {
            'ticket': str(random.randint(12345678, 87654321)),
            'symbol': 'BTCUSDc',
            'type': random.choice(['BUY', 'SELL']),
            'entry_price': round(random.uniform(60000, 65000), 2),
            'exit_price': round(random.uniform(60000, 65000), 2) if random.random() > 0.5 else None,
            'profit': round(random.uniform(-50, 150), 2) if random.random() > 0.5 else None,
            'volume': round(random.uniform(0.01, 0.1), 3),
            'created_at': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            'exit_time': (datetime.now() - timedelta(minutes=random.randint(1, 1440))).isoformat() if random.random() > 0.5 else None,
            'exit_reason': random.choice(['TP', 'SL', 'MANUAL', None])
        }
        trades.append(trade)

    return JsonResponse({
        'success': True,
        'trades': trades,  # Changed from 'data' to 'trades'
        'count': len(trades),
        'summary': {
            'total_trades': len(trades),
            'winning_trades': len([t for t in trades if t['profit'] and t['profit'] > 0]),
            'total_profit': sum([t['profit'] or 0 for t in trades]),
            'win_rate': round(len([t for t in trades if t['profit'] and t['profit'] > 0]) / len(trades) * 100, 1)
        }
    })

def mlp_analytics(request: HttpRequest) -> JsonResponse:
    """Analytics do sistema"""
    import random
    days = int(request.GET.get('days', 7))
    analytics = []

    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_data = {
            'date': date,
            'total_analyses': random.randint(10, 50),
            'total_trades': random.randint(1, 10),
            'buy_signals': random.randint(5, 25),
            'sell_signals': random.randint(5, 25),
            'win_rate': round(random.uniform(0.4, 0.85), 3),
            'total_profit': round(random.uniform(-100, 300), 2)
        }
        analytics.append(day_data)

    return JsonResponse({
        'success': True,
        'data': analytics,
        'period_days': days
    })

def mlp_get_analysis(request: HttpRequest) -> JsonResponse:
    """Obtém análise mais recente"""
    symbol = request.GET.get('symbol', 'BTCUSDc')

    # Dados simulados de análise recente
    analysis = {
        'id': random.randint(1000, 9999),
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'signal': random.choice(['BUY', 'SELL', 'HOLD']),
        'confidence': round(random.uniform(0.6, 0.95), 2),
        'indicators': {
            'rsi': round(random.uniform(30, 70), 1),
            'macd_signal': round(random.uniform(-0.001, 0.001), 4),
            'bb_upper': round(random.uniform(60000, 65000), 2),
            'bb_lower': round(random.uniform(55000, 60000), 2),
        },
        'price_data': {
            'close': round(random.uniform(60000, 65000), 2),
            'open': round(random.uniform(60000, 65000), 2),
            'high': round(random.uniform(62000, 67000), 2),
            'low': round(random.uniform(58000, 62000), 2),
            'volume': random.randint(1000000, 5000000)
        }
    }

    return JsonResponse({
        'success': True,
        'data': analysis,
        'has_data': True
    })

# Views de controle do bot (simuladas)
@csrf_exempt
def mlp_bot_start(request: HttpRequest) -> JsonResponse:
    """Inicia o bot (simulado)"""
    return JsonResponse({
        'success': True,
        'message': 'Bot MLP iniciado',
        'timestamp': datetime.now().isoformat()
    })

@csrf_exempt
def mlp_bot_stop(request: HttpRequest) -> JsonResponse:
    """Para o bot (simulado)"""
    return JsonResponse({
        'success': True,
        'message': 'Bot MLP parado',
        'timestamp': datetime.now().isoformat()
    })

def mlp_status(request: HttpRequest) -> JsonResponse:
    """Status do bot (simulado)"""
    return JsonResponse({
        'success': True,
        'is_running': True,
        'mt5_connected': True,
        'last_update': datetime.now().isoformat()
    })

def mlp_analytics_api(request: HttpRequest) -> JsonResponse:
    """Analytics API (legacy)"""
    return mlp_analytics(request)

# Real-time API endpoints for dashboard
def mlp_api_logs(request: HttpRequest) -> JsonResponse:
    """Retorna logs recentes para display em tempo real"""
    try:
        # Lê arquivo de logs ou usa dados simulados
        logs = []
        import random

        # Simula logs do sistema
        log_levels = ['INFO', 'WARNING', 'ERROR']
        log_messages = [
            'MT5 conectado com sucesso',
            'Análise MLP executada: SELL 88.0%',
            'Critérios atendidos: SELL 88.0%',
            'Tentando conectar ao MT5...',
            'MT5 Trade falhou: 10016',
            'Trade executado - aguardando próximo ciclo',
            'Bot habilitado mas não em modo automático',
            'Analise: BUY 72.0% confiança',
            'Análise salva: ID 58'
        ]

        # Gera logs simulados dos últimos minutos
        for i in range(15):
            logs.append({
                'timestamp': (datetime.now() - timedelta(seconds=random.randint(0, 300))).isoformat(),
                'level': random.choice(log_levels + ['INFO']*5),  # Mais INFO
                'message': random.choice(log_messages)
            })

        # Ordena por timestamp
        logs.sort(key=lambda x: x['timestamp'])

        return JsonResponse({
            'success': True,
            'logs': logs[-20:]  # Últimos 20 logs
        })

    except Exception as e:
        logger.error(f"Erro ao obter logs: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def mlp_api_analysis_latest(request: HttpRequest) -> JsonResponse:
    """Retorna análise mais recente para display em tempo real"""
    try:
        import random

        # Simula análise mais recente
        analysis = {
            'id': random.randint(1000, 9999),
            'timestamp': datetime.now().isoformat(),
            'symbol': 'BTCUSDc',
            'signal': random.choice(['BUY', 'SELL', 'HOLD']),
            'confidence': round(random.uniform(0.65, 0.95), 2) * 100,  # Em porcentagem
            'indicators': {
                'rsi': round(random.uniform(30, 70), 1),
                'macd_signal': round(random.uniform(-0.001, 0.001), 4),
                'bb_upper': round(random.uniform(62000, 67000), 2),
                'bb_lower': round(random.uniform(57000, 62000), 2),
            },
            'price_data': {
                'close': round(random.uniform(60000, 65000), 2),
                'open': round(random.uniform(60000, 65000), 2),
                'high': round(random.uniform(62000, 67000), 2),
                'low': round(random.uniform(58000, 62000), 2),
                'volume': random.randint(1000000, 5000000),
                'change_percent': round(random.uniform(-2, 2), 2),
                'spread': random.randint(1, 5)
            }
        }

        return JsonResponse({
            'success': True,
            'analysis': analysis
        })

    except Exception as e:
        logger.error(f"Erro ao obter análise mais recente: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def mlp_api_status(request: HttpRequest) -> JsonResponse:
    """Retorna status do sistema em tempo real"""
    try:
        from .mlp_bot import mlp_bot

        # Obtém status do bot
        try:
            bot_status = mlp_bot.get_status() if hasattr(mlp_bot, 'get_status') else {'is_running': False}
            is_running = bot_status.get('is_running', False)
        except:
            is_running = False

        return JsonResponse({
            'success': True,
            'is_running': is_running,
            'mt5_connected': True,  # Simulando conexão MT5
            'last_update': datetime.now().isoformat(),
            'uptime': '2h 15m',  # Simulado
            'memory_usage': '45MB'  # Simulado
        })

    except Exception as e:
        logger.error(f"Erro ao obter status do sistema: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
