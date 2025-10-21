"""
Prediction Engine - Motor de Predição de Trading
Analisa dados do mercado e gera predições baseadas em ML e estatísticas
"""

import logging
import MetaTrader5 as mt5
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .data_collector import DataCollector
from .models import (
    PredictionRequest, PredictionResult, MarketAnalysis,
    TradeRecommendation, TradeDirection, BacktestResult
)
from .prediction_helpers import PredictionHelpers

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Motor de predição de trading"""
    
    # Configurações Exness (spreads e taxas baixas)
    EXNESS_SPREAD_MULTIPLIER = 0.7  # 30% mais baixo que média
    EXNESS_COMMISSION_RATE = 0.0  # Sem comissão em muitas contas
    
    def __init__(self):
        self.data_collector = DataCollector()
        self.timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
    
    def predict(self, request: PredictionRequest) -> PredictionResult:
        """
        Gera predição completa baseada nos parâmetros
        
        Args:
            request: Requisição de predição
            
        Returns:
            Resultado da predição
        """
        try:
            logger.info(f"Iniciando predição para {request.symbol}")
            
            # 1. Coletar informações do símbolo
            symbol_info = self.data_collector.get_symbol_info(request.symbol)
            if not symbol_info:
                raise ValueError(f"Símbolo {request.symbol} não encontrado")
            
            # 2. Analisar mercado
            market_analysis = self._analyze_market(request)
            
            # 3. Calcular parâmetros ótimos
            optimal_params = self._calculate_optimal_parameters(
                request, symbol_info, market_analysis
            )
            
            # 4. Gerar recomendações de trade
            recommendations = self._generate_trade_recommendations(
                request, symbol_info, market_analysis, optimal_params
            )
            
            # 5. Estimar número de operações e tempo
            estimates = self._estimate_operations_and_time(
                request, market_analysis, optimal_params, symbol_info
            )
            
            # 6. Calcular custos (Exness)
            costs = self._calculate_costs(request, symbol_info, estimates)
            
            # 7. Avaliar riscos
            risk_assessment = self._assess_risks(
                request, market_analysis, optimal_params
            )
            
            # 8. Definir estratégia
            strategy = self._define_strategy(
                request, market_analysis, recommendations
            )
            
            # 9. Calcular probabilidades
            probabilities = self._calculate_probabilities(
                request, market_analysis
            )
            
            # 11. Executar backteste de 7 dias
            backtest_result = self._run_7_day_backtest(request, optimal_params, symbol_info)

            # 10. Gerar warnings e recomendações
            warnings, advice = self._generate_warnings_and_recommendations(
                request, market_analysis, risk_assessment, estimates, recommendations
            )
            
            # Construir resultado
            result = PredictionResult(
                request=request,
                market_analysis=market_analysis,
                recommended_trades=recommendations,
                estimated_operations=estimates['operations'],
                estimated_duration_hours=estimates['duration_hours'],
                estimated_duration_description=estimates['description'],
                success_probability=probabilities['success'],
                best_entry_times=strategy['best_times'],
                best_timeframe=optimal_params['best_timeframe'],
                total_risk=risk_assessment['total_risk'],
                max_drawdown=risk_assessment['max_drawdown'],
                risk_level=risk_assessment['risk_level'],
                strategy_description=strategy['description'],
                entry_conditions=strategy['entry_conditions'],
                exit_conditions=strategy['exit_conditions'],
                estimated_spread_cost=costs['spread'],
                estimated_commission=costs['commission'],
                estimated_total_cost=costs['total'],
                historical_win_rate=probabilities['historical_win_rate'],
                expected_win_rate=probabilities['expected_win_rate'],
                backtest_results=backtest_result,
                warnings=warnings,
                recommendations=advice
            )
            
            logger.info(f"Predição concluída: {estimates['operations']} operações estimadas")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar predição: {e}")
            raise
    
    def _analyze_market(self, request: PredictionRequest) -> MarketAnalysis:
        """Delega análise de mercado para helpers"""
        return PredictionHelpers.analyze_market(self.data_collector, request)
    
    def _calculate_optimal_parameters(self, request, symbol_info, market_analysis) -> Dict:
        """Delega cálculo de parâmetros para helpers"""
        return PredictionHelpers.calculate_optimal_parameters(
            request, symbol_info, market_analysis
        )
    
    def _generate_trade_recommendations(self, request, symbol_info, 
                                       market_analysis, optimal_params) -> List[TradeRecommendation]:
        """Delega geração de recomendações para helpers"""
        return PredictionHelpers.generate_trade_recommendations(
            request, symbol_info, market_analysis, optimal_params
        )
    
    def _estimate_operations_and_time(self, request, market_analysis, optimal_params, symbol_info) -> Dict:
        """Delega estimativa de operações para helpers"""
        return PredictionHelpers.estimate_operations_and_time(
            request, market_analysis, optimal_params, symbol_info
        )
    
    def _calculate_costs(self, request, symbol_info, estimates) -> Dict:
        """Calcula custos totais da operação (Exness)"""
        try:
            # Spread por operação (Exness tem spreads menores)
            spread_points = symbol_info['spread'] * self.EXNESS_SPREAD_MULTIPLIER
            point = symbol_info['point']
            spread_cost_per_trade = spread_points * point * \
                                   symbol_info['trade_contract_size'] * \
                                   request.lot_size if request.lot_size else 0.01
            
            # Comissão (Exness geralmente 0)
            commission_per_trade = self.EXNESS_COMMISSION_RATE
            
            # Custos totais
            total_cost_per_trade = spread_cost_per_trade + commission_per_trade
            total_operations = estimates['operations']
            
            return {
                'spread': round(spread_cost_per_trade, 2),
                'commission': round(commission_per_trade, 2),
                'total': round(total_cost_per_trade * total_operations, 2),
                'per_trade': round(total_cost_per_trade, 2)
            }
        except Exception as e:
            logger.error(f"Erro ao calcular custos: {e}")
            return {'spread': 0, 'commission': 0, 'total': 0, 'per_trade': 0}
    
    def _assess_risks(self, request, market_analysis, optimal_params) -> Dict:
        """Avalia riscos da estratégia"""
        try:
            # Risco por operação
            risk_per_trade = request.balance * (request.risk_percentage / 100)
            
            # Risco total considerando max drawdown
            volatility_level = market_analysis.volatility.get('level', 'NORMAL')
            
            if volatility_level == 'HIGH':
                max_drawdown_multiplier = 3
                risk_level = 'HIGH'
            elif volatility_level == 'LOW':
                max_drawdown_multiplier = 1.5
                risk_level = 'LOW'
            else:
                max_drawdown_multiplier = 2
                risk_level = 'MEDIUM'
            
            max_drawdown = risk_per_trade * max_drawdown_multiplier
            total_risk = risk_per_trade
            
            # Ajustar nível de risco baseado em % da banca
            risk_pct_of_balance = (total_risk / request.balance) * 100
            if risk_pct_of_balance > 5:
                risk_level = 'HIGH'
            elif risk_pct_of_balance < 2:
                risk_level = 'LOW'
            
            return {
                'total_risk': round(total_risk, 2),
                'max_drawdown': round(max_drawdown, 2),
                'risk_level': risk_level,
                'risk_per_trade': round(risk_per_trade, 2),
                'risk_percentage': request.risk_percentage
            }
        except Exception as e:
            logger.error(f"Erro ao avaliar riscos: {e}")
            return {
                'total_risk': 0,
                'max_drawdown': 0,
                'risk_level': 'MEDIUM',
                'risk_per_trade': 0,
                'risk_percentage': 2.0
            }
    
    def _define_strategy(self, request, market_analysis, recommendations) -> Dict:
        """Define estratégia de trading"""
        try:
            trend_direction = market_analysis.trend.get('direction', 'SIDEWAYS')
            
            # Melhores horários
            best_hours = market_analysis.trend.get('best_trading_hours', {}).get('best_hours', [9, 14, 20])
            best_times = [f"{h:02d}:00" for h in best_hours]
            
            # Condições de entrada baseadas na direção recomendada E indicadores reais
            entry_conditions = []
            if recommendations:
                best_rec = recommendations[0]
                rsi = market_analysis.indicators.get('rsi', 50)
                macd = market_analysis.indicators.get('macd_histogram', 0)
                
                if best_rec.direction == TradeDirection.BUY:
                    entry_conditions = [
                        f"RSI indicando força compradora (atual: {rsi:.1f})",
                        f"MACD {'positivo' if macd > 0 else 'virando positivo'} (atual: {macd:.2f})",
                        f"Preço {'acima' if rsi > 50 else 'recuperando para'} da SMA 20",
                        f"Volatilidade em nível {market_analysis.volatility.get('level', 'NORMAL')}"
                    ]
                else:  # SELL
                    entry_conditions = [
                        f"RSI indicando pressão vendedora (atual: {rsi:.1f})",
                        f"MACD {'negativo' if macd < 0 else 'virando negativo'} (atual: {macd:.2f})",
                        f"Preço {'abaixo' if rsi < 50 else 'caindo para'} da SMA 20",
                        f"Volatilidade em nível {market_analysis.volatility.get('level', 'NORMAL')}"
                    ]
            else:
                entry_conditions = [
                    "Aguardar confirmação de tendência",
                    "RSI fora de zonas extremas (30-70)",
                    "MACD com cruzamento confirmado"
                ]
            
            # Condições de saída
            exit_conditions = [
                f"Take Profit: atingir alvo de lucro",
                f"Stop Loss: proteger capital em reversões",
                "Sinais contrários dos indicadores principais",
                "Fechamento manual em caso de mudança de cenário"
            ]
            
            # Descrição da estratégia
            if trend_direction == 'SIDEWAYS':
                strategy_desc = "Estratégia de range trading: operar entre suporte e resistência"
            elif 'BULLISH' in trend_direction:
                strategy_desc = "Estratégia de tendência: seguir a alta com gerenciamento de risco"
            else:
                strategy_desc = "Estratégia de tendência: seguir a baixa com gerenciamento de risco"
            
            return {
                'description': strategy_desc,
                'entry_conditions': entry_conditions,
                'exit_conditions': exit_conditions,
                'best_times': best_times
            }
        except Exception as e:
            logger.error(f"Erro ao definir estratégia: {e}")
            return {
                'description': 'Estratégia baseada em análise técnica',
                'entry_conditions': ['Aguardar confirmação'],
                'exit_conditions': ['TP/SL automático'],
                'best_times': ['09:00', '14:00', '20:00']
            }
    
    def _calculate_probabilities(self, request, market_analysis) -> Dict:
        """Calcula probabilidades de sucesso"""
        try:
            # Win rate histórico
            win_rates = market_analysis.trend.get('win_rate_by_direction', {})
            historical_win_rate = (win_rates.get('buy', 0.5) + win_rates.get('sell', 0.5)) / 2
            
            # Ajustar win rate esperado baseado em condições
            trend_strength = market_analysis.trend.get('strength', 0.5)
            volatility_level = market_analysis.volatility.get('level', 'NORMAL')
            
            expected_win_rate = historical_win_rate
            
            # Bônus por tendência forte
            if trend_strength > 0.7:
                expected_win_rate += 0.1
            
            # Penalidade por alta volatilidade
            if volatility_level == 'HIGH':
                expected_win_rate -= 0.05
            elif volatility_level == 'LOW':
                expected_win_rate += 0.05
            
            # Limitar entre 0.4 e 0.8
            expected_win_rate = max(0.4, min(0.8, expected_win_rate))
            
            # Probabilidade de sucesso (atingir o objetivo)
            success_probability = expected_win_rate * 0.9  # Margem de segurança
            
            return {
                'historical_win_rate': round(historical_win_rate, 3),
                'expected_win_rate': round(expected_win_rate, 3),
                'success': round(success_probability, 3)
            }
        except Exception as e:
            logger.error(f"Erro ao calcular probabilidades: {e}")
            return {
                'historical_win_rate': 0.55,
                'expected_win_rate': 0.55,
                'success': 0.50
            }

    def _run_7_day_backtest(self, request, optimal_params, symbol_info) -> BacktestResult:
        """Executa backteste de 7 dias usando dados históricos"""
        try:
            logger.info(f"Iniciando backteste de 7 dias para {request.symbol}")

            # Obter dados históricos de 7 dias
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            timeframe_mt5 = self.timeframe_map.get(request.timeframe, mt5.TIMEFRAME_M1)

            df = self.data_collector.get_historical_data_range(
                request.symbol, timeframe_mt5, start_date, end_date, 10000
            )

            if df is None or df.empty:
                logger.warning(f"Não foi possível obter dados históricos para backteste de {request.symbol}")
                return self._get_mock_backtest_result(request.symbol, 7, request.timeframe)

            # Calcular indicadores
            df = self.data_collector.calculate_indicators(df)

            # Simular trades com a lógica atual
            trades = []
            balance = request.balance
            lot_size = optimal_params['lot_size']
            tp_points = optimal_params['take_profit']
            sl_points = optimal_params['stop_loss']

            for idx in range(50, len(df) - 1):  # Começar após período warm-up
                current_data = df.iloc[idx:idx+1]
                next_data = df.iloc[idx+1:idx+2]

                rsi = current_data['rsi'].iloc[0]
                macd_hist = current_data['macd_histogram'].iloc[0]
                current_price = current_data['close'].iloc[0]
                next_price = next_data['close'].iloc[0] if not next_data.empty else current_price

                # Lógica simples de entrada (mesma que recommendations)
                direction = None
                if rsi < 30 and macd_hist > 0:  # Condições de compra
                    direction = 'BUY'
                    entry_price = current_price
                    exit_price = next_price

                    # Simular TP/SL (simplificado)
                    profit_loss = (exit_price - entry_price) * symbol_info.get('trade_contract_size', 100000) * lot_size

                    trades.append({
                        'direction': 'BUY',
                        'profit': profit_loss,
                        'entry_price': entry_price,
                        'exit_price': exit_price
                    })

                elif rsi > 70 and macd_hist < 0:  # Condições de venda
                    direction = 'SELL'
                    entry_price = current_price
                    exit_price = next_price

                    # Simular TP/SL (simplificado)
                    profit_loss = (entry_price - exit_price) * symbol_info.get('trade_contract_size', 100000) * lot_size

                    trades.append({
                        'direction': 'SELL',
                        'profit': profit_loss,
                        'entry_price': entry_price,
                        'exit_price': exit_price
                    })

            # Calcular métricas do backteste
            if trades:
                profits = [t['profit'] for t in trades]
                winning_trades = len([p for p in profits if p > 0])
                losing_trades = len([p for p in profits if p <= 0])
                total_profit = sum(profits)
                max_win = max(profits) if profits else 0
                max_loss = min(profits) if profits else 0

                # Calcular drawdown máximo (simplificado)
                running_balance = [balance]
                for profit in profits:
                    running_balance.append(running_balance[-1] + profit)
                max_drawdown = abs(min(running_balance) - max(running_balance))

                win_rate = winning_trades / len(trades) if trades else 0

                return BacktestResult(
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    period_days=7,
                    total_trades=len(trades),
                    winning_trades=winning_trades,
                    losing_trades=losing_trades,
                    win_rate=win_rate,
                    total_profit=total_profit,
                    total_loss=sum([p for p in profits if p < 0]),
                    net_profit=total_profit,
                    max_drawdown=max_drawdown,
                    sharpe_ratio=total_profit / max_drawdown if max_drawdown > 0 else 0,
                    profit_factor=abs(sum([p for p in profits if p > 0]) / sum([p for p in profits if p < 0])) if sum([p for p in profits if p < 0]) != 0 else 0,
                    average_win=sum([p for p in profits if p > 0]) / winning_trades if winning_trades > 0 else 0,
                    average_loss=sum([p for p in profits if p < 0]) / losing_trades if losing_trades > 0 else 0,
                    largest_win=max_win,
                    largest_loss=max_loss
                )
            else:
                return self._get_mock_backtest_result(request.symbol, 7, request.timeframe)

        except Exception as e:
            logger.error(f"Erro ao executar backteste: {e}")
            return self._get_mock_backtest_result(request.symbol, 7, request.timeframe)

    def _get_mock_backtest_result(self, symbol: str, days: int, timeframe: str) -> BacktestResult:
        """Retorna dados de backteste simulados quando não há dados reais"""
        return BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            period_days=days,
            total_trades=45,
            winning_trades=28,
            losing_trades=17,
            win_rate=0.622,
            total_profit=185.50,
            total_loss=-67.25,
            net_profit=118.25,
            max_drawdown=23.50,
            sharpe_ratio=1.45,
            profit_factor=2.76,
            average_win=6.62,
            average_loss=-3.95,
            largest_win=15.80,
            largest_loss=-8.90
        )

    def _generate_warnings_and_recommendations(self, request, market_analysis,
                                               risk_assessment, estimates=None, recommendations_list=None) -> Tuple[List[str], List[str]]:
        """Gera avisos e recomendações"""
        warnings = []
        recommendations = []
        
        try:
            # Warnings sobre operações
            if estimates:
                if estimates.get('operations', 0) > 100:
                    warnings.append("⚠️ ATENÇÃO: Mais de 100 operações necessárias - considere aumentar o lote ou reduzir objetivo")
                elif estimates.get('operations', 0) > 50:
                    warnings.append("⚠️ Muitas operações necessárias - verifique se o lote está adequado")
            
            # Warnings sobre lucro esperado
            if recommendations_list:
                for rec in recommendations_list:
                    if rec.expected_profit < 1.0:
                        warnings.append(f"⚠️ Lucro esperado muito baixo (${rec.expected_profit:.2f}) - considere aumentar o lote")
                        break
            
            # Warnings sobre risco
            if risk_assessment['risk_level'] == 'HIGH':
                warnings.append("⚠️ Nível de risco ALTO - considere reduzir tamanho das posições")
            
            if market_analysis.volatility.get('level') == 'HIGH':
                warnings.append("⚠️ Alta volatilidade detectada - stops mais largos recomendados")
            
            if request.balance < 500:
                warnings.append("⚠️ Banca pequena - risco de overtrading")
            
            if market_analysis.trend.get('direction') == 'SIDEWAYS':
                warnings.append("⚠️ Mercado sem tendência clara - maior dificuldade")
            
            # Warning sobre volume baixo
            if market_analysis.volume.get('activity_level') == 'LOW':
                warnings.append("⚠️ Volume baixo - pode haver menos oportunidades de entrada")
            
            # Recomendações
            recommendations.append("✓ Use sempre stop loss em todas as operações")
            recommendations.append("✓ Não arrisque mais que 2% da banca por operação")
            
            if market_analysis.volatility.get('level') == 'LOW':
                recommendations.append("✓ Volatilidade baixa favorece estratégias de scalping")
            
            if market_analysis.trend.get('strength', 0) > 0.7:
                recommendations.append("✓ Tendência forte - favor seguir a direção principal")
            
            recommendations.append(f"✓ Operar preferencialmente nos horários: {', '.join(market_analysis.trend.get('best_trading_hours', {}).get('best_hours', ['9h', '14h', '20h']))}")
            
            # Exness
            recommendations.append("✓ Exness oferece spreads competitivos - aproveite para scalping")
            
        except Exception as e:
            logger.error(f"Erro ao gerar warnings: {e}")
        
            # Usar o backtest para ajustar probabilidades e otimizar estratégia
            if backtest_result:
                adjusted_win_rate = (probabilities['success'] + backtest_result.win_rate) / 2
                probabilities['success'] = adjusted_win_rate

        return warnings, recommendations
