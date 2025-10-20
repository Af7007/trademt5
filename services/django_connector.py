"""
Conector para persistir dados MLP no banco Django
Banco local independente na pasta atual do projeto
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal

import logging
logger = logging.getLogger(__name__)

# Verificar se banco local existe
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
db_exists = os.path.exists(db_path)

try:
    # Configurar Django com settings locais
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_settings')

    import django
    from django.conf import settings as django_settings

    # Configurar database local
    django_settings.DATABASES['default']['NAME'] = db_path
    django_settings.configure(
        SECRET_KEY='django-mlp-secret-key',
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'services.quant_app',
        ],
        USE_TZ=True,
        TIME_ZONE='America/Sao_Paulo',
    )

    django.setup()

    django_ready = True
    logger.info(f"Django configurado com sucesso - DB: {db_path}")

    from quant_app.models import MLPAnalysis, MLPTrade, MLPDailyStats
    logger.info("Modelos Django MLP importados com sucesso")

except Exception as e:
    django_ready = False
    django_connector = None
    logger.error(f"Django não disponível: {e}")
    print(f"CRITICAL: Django não configurado - {e}")

logger = logging.getLogger(__name__)


class DjangoMLPConnector:
    """
    Conector para persistir dados do MLP no banco Django
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def save_analysis(self, analysis_data: Dict[str, Any]) -> int:
        """
        Salva uma análise MLP no banco Django

        Args:
            analysis_data: Dados da análise

        Returns:
            ID da análise salva
        """
        try:
            # Serializar dados JSON se necessário
            market_conditions_json = None
            if 'market_conditions' in analysis_data and analysis_data['market_conditions']:
                market_conditions_json = json.dumps(analysis_data['market_conditions'], default=str)

            technical_signals_json = None
            if 'technical_signals' in analysis_data and analysis_data['technical_signals']:
                technical_signals_json = json.dumps(analysis_data['technical_signals'], default=str)

            # Criar análise no Django
            analysis = MLPAnalysis.objects.create(
                symbol=analysis_data['symbol'],
                timeframe='M1',  # Por padrão M1
                signal=analysis_data['signal'],
                confidence=Decimal(str(analysis_data['confidence'])),

                # Metadados do modelo
                model_version=analysis_data.get('model_version'),

                # Indicadores técnicos
                rsi=Decimal(str(analysis_data['indicators'].get('rsi', 0))) if analysis_data['indicators'].get('rsi') else None,
                macd_signal=Decimal(str(analysis_data['indicators'].get('macd_signal', 0))) if analysis_data['indicators'].get('macd_signal') else None,
                bb_upper=Decimal(str(analysis_data['indicators'].get('bb_upper', 0))) if analysis_data['indicators'].get('bb_upper') else None,
                bb_lower=Decimal(str(analysis_data['indicators'].get('bb_lower', 0))) if analysis_data['indicators'].get('bb_lower') else None,
                sma_20=Decimal(str(analysis_data['indicators'].get('sma_20', 0))) if analysis_data['indicators'].get('sma_20') else None,
                sma_50=Decimal(str(analysis_data['indicators'].get('sma_50', 0))) if analysis_data['indicators'].get('sma_50') else None,

                # Preços OHLCV
                price_open=Decimal(str(analysis_data['market_data'].get('open', 0))) if analysis_data['market_data'].get('open') else None,
                price_high=Decimal(str(analysis_data['market_data'].get('high', 0))) if analysis_data['market_data'].get('high') else None,
                price_low=Decimal(str(analysis_data['market_data'].get('low', 0))) if analysis_data['market_data'].get('low') else None,
                price_close=Decimal(str(analysis_data['market_data'].get('close', 0))) if analysis_data['market_data'].get('close') else None,
                volume=analysis_data['market_data'].get('volume'),

                # Dados JSON
                market_conditions=market_conditions_json,
                technical_signals=technical_signals_json,
            )

            self.logger.info(f"Análise MLP salva - ID: {analysis.id}, Signal: {analysis.signal}")
            return analysis.id

        except Exception as e:
            self.logger.error(f"Erro ao salvar análise MLP: {str(e)}")
            raise

    def save_trade(self, trade_data: Dict[str, Any], analysis_id: int) -> int:
        """
        Salva um trade MLP no banco Django

        Args:
            trade_data: Dados do trade
            analysis_id: ID da análise que originou o trade

        Returns:
            ID do trade salvo
        """
        try:
            # Criar trade no Django
            trade = MLPTrade.objects.create(
                ticket=trade_data['ticket'],
                symbol=trade_data['symbol'],
                type=trade_data['type'],
                volume=Decimal(str(trade_data['volume'])),

                # Referência à análise
                analysis_id=analysis_id,

                # Preços
                entry_price=Decimal(str(trade_data['entry_price'])),
                sl_price=Decimal(str(trade_data.get('sl_price', 0))) if trade_data.get('sl_price') else None,
                tp_price=Decimal(str(trade_data.get('tp_price', 0))) if trade_data.get('tp_price') else None,
            )

            self.logger.info(f"Trade MLP salvo - ID: {trade.id}, Ticket: {trade.ticket}")
            return trade.id

        except Exception as e:
            self.logger.error(f"Erro ao salvar trade MLP: {str(e)}")
            raise

    def update_trade_profit(self, ticket: int, profit: float, exit_price: float = None, exit_reason: str = None):
        """
        Atualiza o lucro/prejuízo de um trade

        Args:
            ticket: Ticket do trade
            profit: Lucro/prejuízo
            exit_price: Preço de saída (opcional)
            exit_reason: Razão do fechamento (opcional)
        """
        try:
            trade = MLPTrade.objects.get(ticket=ticket)
            trade.profit = Decimal(str(profit))

            if exit_price:
                trade.exit_price = Decimal(str(exit_price))

            if exit_reason:
                trade.exit_reason = exit_reason.upper()
                trade.exit_time = datetime.now()

            trade.save()

            self.logger.info(f"Trade atualizado - Ticket: {ticket}, Profit: ${profit}")

        except MLPTrade.DoesNotExist:
            self.logger.warning(f"Trade não encontrado - Ticket: {ticket}")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar trade {ticket}: {str(e)}")

    def get_analysis_history(self, symbol: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Recupera histórico de análises

        Args:
            symbol: Filtrar por símbolo (opcional)
            limit: Número máximo de registros

        Returns:
            Lista de análises históricas
        """
        try:
            queryset = MLPAnalysis.objects.order_by('-timestamp')

            if symbol:
                queryset = queryset.filter(symbol=symbol)

            analyses = queryset[:limit]

            # Converter para dict
            result = []
            for analysis in analyses:
                analysis_dict = {
                    'id': analysis.id,
                    'timestamp': analysis.timestamp.isoformat(),
                    'symbol': analysis.symbol,
                    'timeframe': analysis.timeframe,
                    'signal': analysis.signal,
                    'confidence': float(analysis.confidence),
                    'model_version': analysis.model_version,
                    'indicators': {
                        'rsi': float(analysis.rsi) if analysis.rsi else None,
                        'macd_signal': float(analysis.macd_signal) if analysis.macd_signal else None,
                        'bb_upper': float(analysis.bb_upper) if analysis.bb_upper else None,
                        'bb_lower': float(analysis.bb_lower) if analysis.bb_lower else None,
                        'sma_20': float(analysis.sma_20) if analysis.sma_20 else None,
                        'sma_50': float(analysis.sma_50) if analysis.sma_50 else None,
                    },
                    'market_data': {
                        'open': float(analysis.price_open) if analysis.price_open else None,
                        'high': float(analysis.price_high) if analysis.price_high else None,
                        'low': float(analysis.price_low) if analysis.price_low else None,
                        'close': float(analysis.price_close) if analysis.price_close else None,
                        'volume': analysis.volume,
                    }
                }

                # Adicionar dados JSON se existir
                if analysis.market_conditions:
                    try:
                        analysis_dict['market_conditions'] = json.loads(analysis.market_conditions)
                    except:
                        pass

                if analysis.technical_signals:
                    try:
                        analysis_dict['technical_signals'] = json.loads(analysis.technical_signals)
                    except:
                        pass

                result.append(analysis_dict)

            return result

        except Exception as e:
            self.logger.error(f"Erro ao recuperar histórico: {str(e)}")
            return []

    def get_trade_history(self, symbol: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """
        Recupera histórico de trades

        Args:
            symbol: Filtrar por símbolo (opcional)
            days: Dias de histórico

        Returns:
            Lista de trades históricos
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            queryset = MLPTrade.objects.filter(created_at__gte=cutoff_date)

            if symbol:
                queryset = queryset.filter(symbol=symbol)

            trades = queryset.order_by('-created_at')

            # Converter para dict
            result = []
            for trade in trades:
                trade_dict = {
                    'id': trade.id,
                    'ticket': trade.ticket,
                    'symbol': trade.symbol,
                    'type': trade.type,
                    'volume': float(trade.volume),
                    'entry_price': float(trade.entry_price),
                    'sl_price': float(trade.sl_price) if trade.sl_price else None,
                    'tp_price': float(trade.tp_price) if trade.tp_price else None,
                    'exit_price': float(trade.exit_price) if trade.exit_price else None,
                    'profit': float(trade.profit) if trade.profit else None,
                    'created_at': trade.created_at.isoformat(),
                    'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                    'exit_reason': trade.exit_reason,
                    'analysis_id': trade.analysis_id,
                }
                result.append(trade_dict)

            return result

        except Exception as e:
            self.logger.error(f"Erro ao recuperar trades: {str(e)}")
            return []

    def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Recupera estatísticas diárias

        Args:
            days: Número de dias de histórico

        Returns:
            Lista de estatísticas diárias
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            # Para recuperar stats, podemos calcular ou usar tabela MLPDailyStats
            # Por enquanto vamos calcular dinamicamente

            # Pegar todas as análises e trades dentro do período
            analyses = MLPAnalysis.objects.filter(timestamp__gte=cutoff_date)
            trades = MLPTrade.objects.filter(created_at__gte=cutoff_date)

            # Agrupar por data
            daily_stats = {}

            # Processar análises
            for analysis in analyses:
                date_key = analysis.timestamp.date()

                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'date': date_key,
                        'total_analyses': 0,
                        'buy_signals': 0,
                        'sell_signals': 0,
                        'hold_signals': 0,
                    }

                daily_stats[date_key]['total_analyses'] += 1

                if analysis.signal == 'BUY':
                    daily_stats[date_key]['buy_signals'] += 1
                elif analysis.signal == 'SELL':
                    daily_stats[date_key]['sell_signals'] += 1
                else:
                    daily_stats[date_key]['hold_signals'] += 1

            # Processar trades
            for trade in trades:
                date_key = trade.created_at.date()

                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        'date': date_key,
                        'total_analyses': 0,
                        'buy_signals': 0,
                        'sell_signals': 0,
                        'hold_signals': 0,
                        'total_trades': 0,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'total_profit': 0.0,
                    }

                daily_stats[date_key]['total_trades'] += 1

                if trade.profit:
                    if trade.profit > 0:
                        daily_stats[date_key]['winning_trades'] += 1
                    else:
                        daily_stats[date_key]['losing_trades'] += 1

                    daily_stats[date_key]['total_profit'] += float(trade.profit)

            # Calcular métricas e converter para lista
            result = []
            for date_key, stats in sorted(daily_stats.items()):
                stats_copy = stats.copy()

                # Calcular win rate
                if stats['total_trades'] > 0:
                    stats_copy['win_rate'] = round((stats['winning_trades'] / stats['total_trades']) * 100, 2)
                    stats_copy['avg_profit'] = round(stats['total_profit'] / stats['total_trades'], 4)

                result.append(stats_copy)

            return result[::-1]  # Reverso para data mais recente primeiro

        except Exception as e:
            self.logger.error(f"Erro ao recuperar estatísticas diárias: {str(e)}")
            return []


# Instância global
django_connector = DjangoMLPConnector()
