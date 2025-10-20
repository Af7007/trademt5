"""
MLP Storage - Persistente SQLite Database
Substitui arquivos JSON por banco SQLite com SQLAlchemy
Versão final com persistência adequada
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

# Database setup
Base = declarative_base()
DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(__file__), '..', 'mlp_data.db')}"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MLPAnalysis(Base):
    """Tabela para armazenar análises MLP"""
    __tablename__ = "mlp_analyses"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timeframe = Column(String, default="M1")
    signal = Column(String)  # BUY, SELL, HOLD
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Indicadores técnicos
    rsi = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    bb_upper = Column(Float, nullable=True)
    bb_lower = Column(Float, nullable=True)
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)

    # Dados do mercado
    price_open = Column(Float, nullable=True)
    price_high = Column(Float, nullable=True)
    price_low = Column(Float, nullable=True)
    price_close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)

    # Dados JSON para extensibilidade
    market_conditions = Column(Text, nullable=True)  # JSON
    technical_signals = Column(Text, nullable=True)  # JSON


class MLPTrade(Base):
    """Tabela para armazenar trades MLP"""
    __tablename__ = "mlp_trades"

    id = Column(Integer, primary_key=True, index=True)
    ticket = Column(String, unique=True, index=True)
    symbol = Column(String, index=True)
    type = Column(String)  # BUY, SELL
    volume = Column(Float)
    entry_price = Column(Float)

    # Stops e targets
    sl_price = Column(Float, nullable=True)
    tp_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)

    # Resultados
    profit = Column(Float, nullable=True)
    exit_reason = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)

    # Referências
    analysis_id = Column(Integer, nullable=True)


class MLPDailyStats(Base):
    """Tabela para estatísticas diárias"""
    __tablename__ = "mlp_daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True)  # YYYY-MM-DD

    # Estatísticas do dia
    total_analyses = Column(Integer, default=0)
    buy_signals = Column(Integer, default=0)
    sell_signals = Column(Integer, default=0)
    hold_signals = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)

    # Métricas calculadas
    win_rate = Column(Float, nullable=True)
    avg_profit = Column(Float, nullable=True)


class MT5TradeHistory(Base):
    """Tabela para histórico de trades da conta MT5 (não apenas do bot)"""
    __tablename__ = "mt5_trade_history"

    id = Column(Integer, primary_key=True, index=True)
    ticket = Column(String, unique=True, index=True)
    order = Column(String, nullable=True)
    symbol = Column(String, index=True)
    type = Column(String)  # BUY, SELL
    entry = Column(String, default="OUT")  # IN, OUT, REVERSAL
    magic = Column(Integer, nullable=True)  # 0 para trades manuais
    volume = Column(Float)
    price = Column(Float)

    # Resultados financeiros
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    profit = Column(Float, default=0.0)
    fee = Column(Float, default=0.0)

    # Informações adicionais
    comment = Column(String, nullable=True)
    external_id = Column(String, nullable=True)
    time = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Índices para performance
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class MLPStorage:
    """Classe de storage persistente usando SQLite"""

    def __init__(self):
        # Criar banco se não existir
        Base.metadata.create_all(bind=engine)

        # Configurações do bot
        self.bot_config = {
            "take_profit": 0.5,
            "confidence_threshold": 0.85,
            "auto_trading_enabled": False,
            "symbol": "BTCUSDc"
        }

    def get_db(self) -> Session:
        """Get database session"""
        return SessionLocal()

    def get_analyses(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Obtém análises MLP filtradas"""
        db = self.get_db()
        try:
            query = db.query(MLPAnalysis).order_by(MLPAnalysis.timestamp.desc())

            if symbol and symbol != 'all':
                query = query.filter(MLPAnalysis.symbol == symbol)

            analyses = query.limit(limit).all()

            result = []
            for analysis in analyses:
                analysis_dict = {
                    'id': analysis.id,
                    'symbol': analysis.symbol,
                    'timeframe': analysis.timeframe,
                    'signal': analysis.signal,
                    'confidence': float(analysis.confidence),
                    'timestamp': analysis.timestamp.isoformat(),

                    # Indicadores
                    'indicators': {
                        'rsi': float(analysis.rsi) if analysis.rsi else None,
                        'macd_signal': float(analysis.macd_signal) if analysis.macd_signal else None,
                        'bb_upper': float(analysis.bb_upper) if analysis.bb_upper else None,
                        'bb_lower': float(analysis.bb_lower) if analysis.bb_lower else None,
                        'sma_20': float(analysis.sma_20) if analysis.sma_20 else None,
                        'sma_50': float(analysis.sma_50) if analysis.sma_50 else None,
                    },

                    # Dados do mercado
                    'market_data': {
                        'open': float(analysis.price_open) if analysis.price_open else None,
                        'high': float(analysis.price_high) if analysis.price_high else None,
                        'low': float(analysis.price_low) if analysis.price_low else None,
                        'close': float(analysis.price_close) if analysis.price_close else None,
                        'volume': float(analysis.volume) if analysis.volume else None,
                    }
                }

                # Adicionar dados JSON se existirem
                if analysis.market_conditions:
                    try:
                        import json
                        analysis_dict['market_conditions'] = json.loads(analysis.market_conditions)
                    except:
                        pass

                if analysis.technical_signals:
                    try:
                        import json
                        analysis_dict['technical_signals'] = json.loads(analysis.technical_signals)
                    except:
                        pass

                result.append(analysis_dict)

            return result

        finally:
            db.close()

    def add_analysis(self, analysis: Dict) -> int:
        """Adiciona nova análise MLP"""
        db = self.get_db()
        try:
            import json
            analysis_obj = MLPAnalysis(
                symbol=analysis['symbol'],
                timeframe=analysis.get('timeframe', 'M1'),
                signal=analysis['signal'],
                confidence=analysis['confidence'],
                timestamp=datetime.fromisoformat(analysis.get('timestamp', datetime.utcnow().isoformat())),

                # Indicadores
                rsi=analysis.get('indicators', {}).get('rsi'),
                macd_signal=analysis.get('indicators', {}).get('macd_signal'),
                bb_upper=analysis.get('indicators', {}).get('bb_upper'),
                bb_lower=analysis.get('indicators', {}).get('bb_lower'),
                sma_20=analysis.get('indicators', {}).get('sma_20'),
                sma_50=analysis.get('indicators', {}).get('sma_50'),

                # Dados OHLCV
                price_open=analysis.get('market_data', {}).get('open'),
                price_high=analysis.get('market_data', {}).get('high'),
                price_low=analysis.get('market_data', {}).get('low'),
                price_close=analysis.get('market_data', {}).get('close'),
                volume=analysis.get('market_data', {}).get('volume'),

                # Dados JSON
                market_conditions=json.dumps(analysis.get('market_conditions')) if analysis.get('market_conditions') else None,
                technical_signals=json.dumps(analysis.get('technical_signals')) if analysis.get('technical_signals') else None,
            )

            db.add(analysis_obj)
            db.commit()
            db.refresh(analysis_obj)

            return analysis_obj.id

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_trades(self, symbol: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Obtém trades MLP filtrados por período"""
        db = self.get_db()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(MLPTrade).filter(MLPTrade.created_at >= cutoff_date)

            if symbol and symbol != 'all':
                query = query.filter(MLPTrade.symbol == symbol)

            trades = query.order_by(MLPTrade.created_at.desc()).all()

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
                    'exit_reason': trade.exit_reason,
                    'created_at': trade.created_at.isoformat(),
                    'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
                    'analysis_id': trade.analysis_id,
                }
                result.append(trade_dict)

            return result

        finally:
            db.close()

    def add_trade(self, trade: Dict) -> int:
        """Adiciona novo trade MLP"""
        db = self.get_db()
        try:
            trade_obj = MLPTrade(
                ticket=trade['ticket'],
                symbol=trade['symbol'],
                type=trade['type'],
                volume=trade['volume'],
                entry_price=trade['entry_price'],
                sl_price=trade.get('sl_price'),
                tp_price=trade.get('tp_price'),
                exit_price=trade.get('exit_price'),
                profit=trade.get('profit'),
                exit_reason=trade.get('exit_reason'),
                analysis_id=trade.get('analysis_id'),
                created_at=datetime.fromisoformat(trade.get('created_at', datetime.utcnow().isoformat())),
                exit_time=datetime.fromisoformat(trade.get('exit_time')) if trade.get('exit_time') else None,
            )

            db.add(trade_obj)
            db.commit()
            db.refresh(trade_obj)

            return trade_obj.id

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def update_trade(self, ticket: str, updates: Dict) -> bool:
        """Atualiza trade existente"""
        db = self.get_db()
        try:
            trade = db.query(MLPTrade).filter(MLPTrade.ticket == ticket).first()

            if not trade:
                return False

            # Aplicar atualizações
            for key, value in updates.items():
                if hasattr(trade, key):
                    if key in ['exit_time'] and isinstance(value, str):
                        value = datetime.fromisoformat(value)
                    setattr(trade, key, value)

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_daily_stats(self, days: int = 30) -> List[Dict]:
        """Obtém estatísticas diárias MLP"""
        db = self.get_db()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            stats = db.query(MLPDailyStats).filter(
                MLPDailyStats.date >= cutoff_date.strftime('%Y-%m-%d')
            ).order_by(MLPDailyStats.date.desc()).all()

            result = []
            for stat in stats:
                stat_dict = {
                    'id': stat.id,
                    'date': stat.date,
                    'total_analyses': stat.total_analyses,
                    'buy_signals': stat.buy_signals,
                    'sell_signals': stat.sell_signals,
                    'hold_signals': stat.hold_signals,
                    'total_trades': stat.total_trades,
                    'winning_trades': stat.winning_trades,
                    'losing_trades': stat.losing_trades,
                    'total_profit': stat.total_profit,
                    'win_rate': float(stat.win_rate) if stat.win_rate else None,
                    'avg_profit': float(stat.avg_profit) if stat.avg_profit else None,
                }
                result.append(stat_dict)

            return result

        finally:
            db.close()

    def add_daily_stats(self, stats: Dict) -> int:
        """Adiciona estatísticas diárias"""
        db = self.get_db()
        try:
            date_str = stats['date']

            # Verificar se já existe
            existing = db.query(MLPDailyStats).filter(MLPDailyStats.date == date_str).first()

            if existing:
                # Atualizar
                for key, value in stats.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                db.commit()
                return existing.id
            else:
                # Criar novo
                stats_obj = MLPDailyStats(**stats)
                db.add(stats_obj)
                db.commit()
                db.refresh(stats_obj)
                return stats_obj.id

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_config(self) -> Dict:
        """Obtém configuração do bot MLP"""
        return self.bot_config.copy()

    def update_config(self, updates: Dict) -> bool:
        """Atualiza configuração do bot MLP"""
        self.bot_config.update(updates)
        return True

    def get_mt5_trade_history(self, symbol: Optional[str] = None, days: int = 30) -> List[Dict]:
        """Obtém histórico de trades MT5 do banco de dados"""
        db = self.get_db()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(MT5TradeHistory).filter(MT5TradeHistory.time >= cutoff_date)

            if symbol and symbol != 'all':
                query = query.filter(MT5TradeHistory.symbol == symbol)

            trades = query.order_by(MT5TradeHistory.time.desc()).all()

            result = []
            for trade in trades:
                trade_dict = {
                    'id': trade.id,
                    'ticket': trade.ticket,
                    'order': trade.order,
                    'symbol': trade.symbol,
                    'type': trade.type,
                    'entry': trade.entry,
                    'magic': trade.magic,
                    'volume': float(trade.volume),
                    'price': float(trade.price),
                    'commission': float(trade.commission),
                    'swap': float(trade.swap),
                    'profit': float(trade.profit),
                    'fee': float(trade.fee),
                    'comment': trade.comment,
                    'external_id': trade.external_id,
                    'time': trade.time.isoformat(),
                    'created_at': trade.created_at.isoformat(),
                    'updated_at': trade.updated_at.isoformat()
                }
                result.append(trade_dict)

            return result

        finally:
            db.close()

    def save_mt5_trade_history(self, deals: List[Dict]) -> int:
        """Salva histórico de trades MT5 no banco (upsert)"""
        db = self.get_db()
        saved_count = 0
        try:
            for deal in deals:
                ticket = str(deal['ticket'])

                # Verificar se já existe
                existing = db.query(MT5TradeHistory).filter(MT5TradeHistory.ticket == ticket).first()

                if existing:
                    # Atualizar apenas se tiver dados mais recentes
                    new_time = datetime.fromtimestamp(deal['time'])
                    if new_time > existing.time:
                        existing.time = new_time
                        existing.updated_at = datetime.utcnow()
                else:
                    # Criar novo
                    trade_obj = MT5TradeHistory(
                        ticket=ticket,
                        order=str(deal.get('order', '')),
                        symbol=deal['symbol'],
                        type=deal['type'],
                        entry=deal['entry'],
                        magic=deal.get('magic'),
                        volume=deal['volume'],
                        price=deal['price'],
                        commission=deal.get('commission', 0.0),
                        swap=deal.get('swap', 0.0),
                        profit=deal.get('profit', 0.0),
                        fee=deal.get('fee', 0.0),
                        comment=deal.get('comment'),
                        external_id=deal.get('external_id'),
                        time=datetime.fromtimestamp(deal['time'])
                    )
                    db.add(trade_obj)
                    saved_count += 1

            db.commit()
            return saved_count

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_mt5_trade_statistics(self, days: int = 30, symbol: Optional[str] = None) -> Dict:
        """Calcula estatísticas de trades MT5"""
        db = self.get_db()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(MT5TradeHistory).filter(
                MT5TradeHistory.time >= cutoff_date,
                MT5TradeHistory.entry == 'OUT'  # Apenas trades finalizados
            )

            if symbol and symbol != 'all':
                query = query.filter(MT5TradeHistory.symbol == symbol)

            trades = query.all()

            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'total_profit': 0.0,
                    'win_rate': 0.0,
                    'avg_profit': 0.0,
                    'avg_loss': 0.0,
                    'largest_win': 0.0,
                    'largest_loss': 0.0
                }

            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.profit > 0])
            losing_trades = total_trades - winning_trades
            total_profit = sum(t.profit for t in trades)
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

            profits = [t.profit for t in trades if t.profit > 0]
            losses = [abs(t.profit) for t in trades if t.profit < 0]

            avg_profit = sum(profits) / len(profits) if profits else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            largest_win = max(profits) if profits else 0
            largest_loss = max(losses) if losses else 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'total_profit': total_profit,
                'win_rate': win_rate,
                'avg_profit': avg_profit,
                'avg_loss': avg_loss,
                'largest_win': largest_win,
                'largest_loss': largest_loss
            }

        finally:
            db.close()


# Instância global
mlp_storage = MLPStorage()
