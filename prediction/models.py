"""
Modelos de dados para o sistema de predição
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TradeDirection(str, Enum):
    """Direção do trade"""
    BUY = "BUY"
    SELL = "SELL"
    BOTH = "BOTH"


class TimeframeType(str, Enum):
    """Tipos de timeframe"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


@dataclass
class PredictionRequest:
    """Requisição de predição"""
    symbol: str
    target_profit: float  # Lucro alvo em USD
    balance: float  # Banca disponível
    timeframe: Optional[str] = "M1"
    lot_size: Optional[float] = None  # Se None, será calculado
    take_profit: Optional[float] = None  # TP em pontos (se None, será calculado)
    stop_loss: Optional[float] = None  # SL em pontos (se None, será calculado)
    max_operations: Optional[int] = None  # Limite de operações (None = sem limite)
    risk_percentage: float = 2.0  # % de risco por operação
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'symbol': self.symbol,
            'target_profit': self.target_profit,
            'balance': self.balance,
            'timeframe': self.timeframe,
            'lot_size': self.lot_size,
            'take_profit': self.take_profit,
            'stop_loss': self.stop_loss,
            'max_operations': self.max_operations,
            'risk_percentage': self.risk_percentage
        }


@dataclass
class TradeRecommendation:
    """Recomendação de trade"""
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    confidence: float  # 0-1
    expected_profit: float
    expected_loss: float
    risk_reward_ratio: float
    reasoning: str
    indicators: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'direction': self.direction.value,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'lot_size': self.lot_size,
            'confidence': self.confidence,
            'expected_profit': self.expected_profit,
            'expected_loss': self.expected_loss,
            'risk_reward_ratio': self.risk_reward_ratio,
            'reasoning': self.reasoning,
            'indicators': self.indicators
        }


@dataclass
class MarketAnalysis:
    """Análise de mercado"""
    symbol: str
    timeframe: str
    trend: Dict[str, Any]
    support_resistance: Dict[str, Any]
    volatility: Dict[str, Any]
    volume: Dict[str, Any]
    indicators: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'trend': self.trend,
            'support_resistance': self.support_resistance,
            'volatility': self.volatility,
            'volume': self.volume,
            'indicators': self.indicators,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PredictionResult:
    """Resultado da predição"""
    request: PredictionRequest
    market_analysis: MarketAnalysis
    
    # Recomendações
    recommended_trades: List[TradeRecommendation]
    
    # Predições
    estimated_operations: int
    estimated_duration_hours: float
    estimated_duration_description: str
    success_probability: float  # 0-1
    
    # Timing
    best_entry_times: List[str]  # Horários recomendados
    best_timeframe: str
    
    # Risk Management
    total_risk: float
    max_drawdown: float
    risk_level: str  # LOW, MEDIUM, HIGH
    
    # Trading Strategy
    strategy_description: str
    entry_conditions: List[str]
    exit_conditions: List[str]
    
    # Spreads e Custos (Exness)
    estimated_spread_cost: float
    estimated_commission: float
    estimated_total_cost: float
    
    # Estatísticas
    historical_win_rate: float
    expected_win_rate: float

    # Backtest Results (opcionais)
    backtest_results: Optional['BacktestResult'] = None

    # Mensagens
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Converte para dicionário completo"""
        return {
            'request': self.request.to_dict(),
            'market_analysis': self.market_analysis.to_dict(),
            'recommended_trades': [t.to_dict() for t in self.recommended_trades],
            'predictions': {
                'estimated_operations': self.estimated_operations,
                'estimated_duration_hours': self.estimated_duration_hours,
                'estimated_duration_description': self.estimated_duration_description,
                'success_probability': self.success_probability,
            },
            'timing': {
                'best_entry_times': self.best_entry_times,
                'best_timeframe': self.best_timeframe
            },
            'risk_management': {
                'total_risk': self.total_risk,
                'max_drawdown': self.max_drawdown,
                'risk_level': self.risk_level
            },
            'strategy': {
                'description': self.strategy_description,
                'entry_conditions': self.entry_conditions,
                'exit_conditions': self.exit_conditions
            },
            'costs': {
                'spread': self.estimated_spread_cost,
                'commission': self.estimated_commission,
                'total': self.estimated_total_cost
            },
            'statistics': {
                'historical_win_rate': self.historical_win_rate,
                'expected_win_rate': self.expected_win_rate
            },
            'backtest_results': self.backtest_results.to_dict() if self.backtest_results else None,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class BacktestResult:
    """Resultado de backtest"""
    symbol: str
    timeframe: str
    period_days: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit: float
    total_loss: float
    net_profit: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'period_days': self.period_days,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_profit': self.net_profit,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'profit_factor': self.profit_factor,
            'average_win': self.average_win,
            'average_loss': self.average_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss
        }
