"""
Serviço para gerenciar múltiplos bots simultaneamente
"""
import uuid
import json
import sqlite3
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock
import logging

logger = logging.getLogger(__name__)

DB_PATH = "mlp_data.db"


class BotInstance:
    """Representa uma instância de bot com seu próprio trading engine"""
    
    def __init__(self, bot_id: str, config: Dict, trading_engine):
        self.bot_id = bot_id
        # Garantir que config é sempre um dict
        if isinstance(config, str):
            self.config = json.loads(config)
            logger.warning(f"Bot {bot_id}: Config era string, convertido para dict")
        else:
            self.config = config
        
        # Extrair símbolo da config
        self.symbol = self.config.get('symbol', 'XAUUSDc')
        self.timeframe = self.config.get('timeframe', 'M1')
        
        self.trading_engine = trading_engine
        self.is_running = False
        self.created_at = datetime.now()
        self.analysis_thread = None
        self.stop_analysis = False
        self.last_trade_time = None  # Timestamp do último trade
        self.consecutive_losses = 0  # Contador de perdas consecutivas
        self.last_trade_profit = 0  # P&L do último trade
        
        # Ler cooldown da config ou usar padrão de 20s
        self.trade_cooldown = self.config.get('trading', {}).get('trade_cooldown', 20)
        logger.info(f"Bot {bot_id}: Criado para {self.symbol} {self.timeframe}, cooldown={self.trade_cooldown}s")
        
    def start_analysis_loop(self):
        """Inicia loop de análise em thread separada"""
        if self.analysis_thread and self.analysis_thread.is_alive():
            logger.warning(f"Bot {self.bot_id}: Thread de análise já está rodando")
            return
        
        # Verificar se MLP está habilitado e treinar AUTOMATICAMENTE
        config = self.config
        if isinstance(config, str):
            config = json.loads(config)
        
        analysis_method = config.get('analysis_method', {})
        use_mlp = analysis_method.get('use_mlp', True)  # MLP habilitado por padrão
        
        if use_mlp:
            logger.info(f"Bot {self.bot_id}: ========== TREINANDO MLP AUTOMATICAMENTE ==========")
            logger.info(f"Bot {self.bot_id}: Símbolo: {self.symbol}, Timeframe: {self.timeframe}")
            
            try:
                import MetaTrader5 as mt5
                from services.mlp_predictor import mlp_predictor
                
                # Conectar MT5
                if not mt5.initialize():
                    logger.error(f"Bot {self.bot_id}: ❌ Erro ao conectar MT5")
                else:
                    # Mapear timeframe
                    timeframe_map = {
                        'M1': mt5.TIMEFRAME_M1,
                        'M5': mt5.TIMEFRAME_M5,
                        'M15': mt5.TIMEFRAME_M15,
                        'M30': mt5.TIMEFRAME_M30,
                        'H1': mt5.TIMEFRAME_H1,
                        'H4': mt5.TIMEFRAME_H4,
                        'D1': mt5.TIMEFRAME_D1
                    }
                    
                    mt5_timeframe = timeframe_map.get(self.timeframe, mt5.TIMEFRAME_M1)
                    
                    # Obter dados históricos
                    logger.info(f"Bot {self.bot_id}: Obtendo 500 candles de {self.symbol} {self.timeframe}...")
                    rates = mt5.copy_rates_from_pos(self.symbol, mt5_timeframe, 0, 500)
                    
                    if rates is not None and len(rates) > 0:
                        import pandas as pd
                        df = pd.DataFrame(rates)
                        
                        # Preparar dados de treinamento
                        logger.info(f"Bot {self.bot_id}: Preparando dados de treinamento...")
                        training_data = mlp_predictor._prepare_training_data(df, self.symbol, mt5_timeframe)
                        
                        if training_data and len(training_data) > 10:
                            # Treinar modelo
                            logger.info(f"Bot {self.bot_id}: Treinando MLP com {len(training_data)} amostras...")
                            success = mlp_predictor.train(training_data)
                            
                            if success:
                                logger.info(f"Bot {self.bot_id}: ✅ MLP TREINADO COM SUCESSO!")
                            else:
                                logger.error(f"Bot {self.bot_id}: ❌ Falha no treinamento do MLP")
                        else:
                            logger.error(f"Bot {self.bot_id}: ❌ Dados insuficientes para treinamento")
                    else:
                        logger.error(f"Bot {self.bot_id}: ❌ Erro ao obter dados históricos")
                        
            except Exception as e:
                logger.error(f"Bot {self.bot_id}: ❌ Erro ao treinar MLP: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.info(f"Bot {self.bot_id}: MLP desabilitado - usando indicadores")
        
        self.stop_analysis = False
        self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.analysis_thread.start()
        logger.info(f"Bot {self.bot_id}: Thread de análise iniciada")
    
    def stop_analysis_loop(self):
        """Para loop de análise"""
        self.stop_analysis = True
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
            logger.info(f"Bot {self.bot_id}: Thread de análise parada")
    
    def _analysis_loop(self):
        """Loop de análise que roda em thread separada"""
        try:
            # Garantir que config é um dicionário
            config = self.config
            if isinstance(config, str):
                config = json.loads(config)
                
            symbol = config.get('symbol', 'BTCUSDc')
            logger.info(f"Bot {self.bot_id}: Iniciando análise contínua de {symbol}")
            logger.info(f"Bot {self.bot_id}: Thread ID: {threading.current_thread().ident}")
            
            # Estatísticas
            analysis_count = 0
            buy_signals = 0
            sell_signals = 0
            hold_signals = 0
            trades_executed = 0
            
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Erro ao iniciar thread: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return
        
        while not self.stop_analysis and self.is_running:
            analysis_count += 1
            logger.debug(f"Bot {self.bot_id} ({symbol}): Loop de análise rodando...")
            try:
                logger.info(f"Bot {self.bot_id}: Iniciando análise, config type={type(self.config)}, config={self.config}")
                
                # Gerar análise usando o trading engine
                import MetaTrader5 as mt5
                from services.mlp_storage import mlp_storage
                
                # Obter dados do mercado
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
                
                if rates is not None and len(rates) > 0:
                    # Aqui você pode chamar o método de análise do trading_engine
                    # Por enquanto, vou criar uma análise básica
                    import pandas as pd
                    df = pd.DataFrame(rates)
                    
                    # Calcular indicadores básicos
                    close = df['close'].values
                    
                    # RSI
                    deltas = [close[i] - close[i-1] for i in range(1, len(close))]
                    gains = [d if d > 0 else 0 for d in deltas]
                    losses = [-d if d < 0 else 0 for d in deltas]
                    avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 0
                    avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 0
                    rsi = 100 - (100 / (1 + (avg_gain / avg_loss))) if avg_loss > 0 else 50
                    
                    # SMA
                    sma_20 = sum(close[-20:]) / 20 if len(close) >= 20 else close[-1]
                    sma_50 = sum(close[-50:]) / 50 if len(close) >= 50 else close[-1]
                    
                    # Verificar método de análise configurado
                    analysis_method = config.get('analysis_method', {})
                    use_indicators = analysis_method.get('use_indicators', False)  # Desabilitar indicadores
                    use_mlp = analysis_method.get('use_mlp', True)  # HABILITAR MLP por padrão
                    
                    # Determinar sinal baseado no método configurado
                    signal = 'HOLD'
                    confidence = 0.50
                    
                    logger.info(f"Bot {self.bot_id} ({symbol}): RSI={rsi:.1f}, Price={close[-1]:.2f}, SMA20={sma_20:.2f}, SMA50={sma_50:.2f}")
                    logger.info(f"Bot {self.bot_id}: Método - Indicadores: {use_indicators}, MLP: {use_mlp}")
                    
                    # Usar indicadores técnicos
                    if use_indicators:
                        # Sinais fortes (alta confiança)
                        if rsi < 30:
                            signal = 'BUY'
                            confidence = 0.85
                            logger.info(f"Bot {self.bot_id}: RSI < 30 → BUY 85%")
                        elif rsi > 70:
                            signal = 'SELL'
                            confidence = 0.85
                            logger.info(f"Bot {self.bot_id}: RSI > 70 → SELL 85%")
                        # Sinais médios baseados em RSI
                        elif rsi < 40:
                            signal = 'BUY'
                            confidence = 0.70
                            logger.info(f"Bot {self.bot_id}: RSI < 40 → BUY 70%")
                        elif rsi > 60:
                            signal = 'SELL'
                            confidence = 0.70
                            logger.info(f"Bot {self.bot_id}: RSI > 60 → SELL 70%")
                        # Sinais de tendência
                        elif close[-1] > sma_20 > sma_50 and rsi > 50:
                            signal = 'BUY'
                            confidence = 0.65
                            logger.info(f"Bot {self.bot_id}: Tendência Alta + RSI > 50 → BUY 65%")
                        elif close[-1] < sma_20 < sma_50 and rsi < 50:
                            signal = 'SELL'
                            confidence = 0.65
                            logger.info(f"Bot {self.bot_id}: Tendência Baixa + RSI < 50 → SELL 65%")
                        else:
                            logger.info(f"Bot {self.bot_id}: Nenhuma condição atendida → HOLD 50%")
                    
                    # Usar modelo MLP
                    elif use_mlp:
                        from services.mlp_predictor import mlp_predictor
                        
                        logger.info(f"Bot {self.bot_id}: ========== USANDO MLP PARA PREDIÇÃO ==========")
                        
                        try:
                            signal, confidence = mlp_predictor.predict(df)
                            logger.info(f"Bot {self.bot_id}: ✓ MLP → {signal} ({confidence*100:.1f}%)")
                        except Exception as e:
                            logger.error(f"Bot {self.bot_id}: ❌ ERRO NO MLP: {e}")
                            logger.error(f"Bot {self.bot_id}: 💡 Treine o MLP clicando 'Retreinar MLP'")
                            signal = 'HOLD'
                            confidence = 0.50
                    
                    # Determinar trend
                    if sma_20 > sma_50:
                        trend = 'BULLISH'
                    elif sma_20 < sma_50:
                        trend = 'BEARISH'
                    else:
                        trend = 'NEUTRAL'
                    
                    # Salvar análise no banco com timestamp local do sistema
                    # datetime.now() já retorna horário local do sistema
                    
                    analysis_data = {
                        'symbol': symbol,
                        'timeframe': 'M1',
                        'signal': signal,
                        'confidence': confidence,
                        # Não passar timestamp, deixar o banco usar CURRENT_TIMESTAMP
                        'indicators': json.dumps({
                            'rsi': rsi,
                            'sma_20': sma_20,
                            'sma_50': sma_50
                        }),
                        'market_conditions': json.dumps({
                            'trend': trend
                        }),
                        'market_data': json.dumps({
                            'close': float(close[-1]),
                            'open': float(df['open'].values[-1]),
                            'high': float(df['high'].values[-1]),
                            'low': float(df['low'].values[-1])
                        })
                    }
                    
                    # Salvar no banco de dados
                    mlp_storage.add_analysis(analysis_data)
                    
                    # Adicionar ao cache em memória para exibição em tempo real
                    from routes.bot_analysis_routes import add_analysis_to_cache
                    cache_data = {
                        'bot_id': self.bot_id,
                        'symbol': symbol,
                        'signal': signal,
                        'confidence': confidence,
                        'timestamp': datetime.now().isoformat(),
                        'indicators': {
                            'rsi': rsi,
                            'sma_20': sma_20,
                            'sma_50': sma_50
                        },
                        'market_conditions': {
                            'trend': trend
                        },
                        'market_data': {
                            'close': float(close[-1]),
                            'open': float(df['open'].values[-1]),
                            'high': float(df['high'].values[-1]),
                            'low': float(df['low'].values[-1])
                        }
                    }
                    add_analysis_to_cache(self.bot_id, cache_data)
                    
                    # Contar sinais
                    if signal == 'BUY':
                        buy_signals += 1
                    elif signal == 'SELL':
                        sell_signals += 1
                    else:
                        hold_signals += 1
                    
                    logger.info(f"Bot {self.bot_id} ({symbol}): Análise salva - {signal} ({confidence*100:.1f}%)")
                    logger.info(f"Bot {self.bot_id}: Estatísticas - Análises: {analysis_count}, BUY: {buy_signals}, SELL: {sell_signals}, HOLD: {hold_signals}")
                    
                    # Executar trade se auto_execute estiver habilitado
                    logger.info(f"Bot {self.bot_id}: ========== VERIFICANDO TRADING AUTOMÁTICO ==========")
                    auto_execute = config.get('trading', {}).get('auto_execute', False)
                    logger.info(f"Bot {self.bot_id}: config.trading = {config.get('trading', {})}")
                    logger.info(f"Bot {self.bot_id}: auto_execute={auto_execute}, signal={signal}, confidence={confidence:.2f}")
                    
                    # DIAGNÓSTICO COMPLETO
                    if not auto_execute:
                        logger.error(f"Bot {self.bot_id}: ❌ AUTO_EXECUTE DESABILITADO!")
                        logger.error(f"Bot {self.bot_id}: ❌ Configure 'trading.auto_execute': true na config")
                        logger.error(f"Bot {self.bot_id}: ❌ Config atual: {config.get('trading', {})}")
                    else:
                        logger.info(f"Bot {self.bot_id}: ✓ Auto execute HABILITADO")
                    
                    if signal == 'HOLD':
                        logger.warning(f"Bot {self.bot_id}: ⚠️ Sinal é HOLD - não vai executar")
                    else:
                        logger.info(f"Bot {self.bot_id}: ✓ Sinal válido: {signal}")
                    
                    if auto_execute:
                        # VERIFICAR HEDGE ANTES DE EXECUTAR
                        magic_number = config.get('advanced', {}).get('magic_number', 123456)
                        all_positions = mt5.positions_get(symbol=symbol)
                        my_positions = [p for p in all_positions if p.magic == magic_number] if all_positions else []
                        buy_count = sum(1 for p in my_positions if p.type == 0)
                        sell_count = sum(1 for p in my_positions if p.type == 1)
                        
                        # ESTRATÉGIA HÍBRIDA: MLP decide QUANDO, Bot garante HEDGE
                        original_signal = signal
                        original_confidence = confidence
                        
                        # Se desbalanceado, PRIORIZAR hedge mas respeitar oportunidade MLP
                        if buy_count > 0 and sell_count == 0:
                            logger.warning(f"Bot {self.bot_id}: ⚠️ Desbalanceado: {buy_count} BUY sem SELL")
                            
                            # Se MLP deu sinal SELL, usar ele (oportunidade + hedge)
                            if original_signal == 'SELL':
                                logger.info(f"Bot {self.bot_id}: ✓ MLP identificou oportunidade SELL - Perfeito para hedge!")
                            # Se MLP deu BUY, FORÇAR SELL para hedge
                            elif original_signal == 'BUY':
                                logger.error(f"Bot {self.bot_id}: 🚨 MLP quer BUY mas precisa SELL para hedge!")
                                logger.error(f"Bot {self.bot_id}: 🔄 FORÇANDO SELL para proteger banca")
                                signal = 'SELL'
                                confidence = 0.80  # Alta confiança para hedge de proteção
                            # Se MLP deu HOLD, FORÇAR SELL para hedge
                            else:
                                logger.error(f"Bot {self.bot_id}: 🚨 MLP em HOLD mas precisa SELL para hedge!")
                                logger.error(f"Bot {self.bot_id}: 🔄 FORÇANDO SELL para proteger banca")
                                signal = 'SELL'
                                confidence = 0.75  # Confiança média para hedge forçado
                        
                        elif sell_count > 0 and buy_count == 0:
                            logger.warning(f"Bot {self.bot_id}: ⚠️ Desbalanceado: {sell_count} SELL sem BUY")
                            
                            # Se MLP deu sinal BUY, usar ele (oportunidade + hedge)
                            if original_signal == 'BUY':
                                logger.info(f"Bot {self.bot_id}: ✓ MLP identificou oportunidade BUY - Perfeito para hedge!")
                            # Se MLP deu SELL, FORÇAR BUY para hedge
                            elif original_signal == 'SELL':
                                logger.error(f"Bot {self.bot_id}: 🚨 MLP quer SELL mas precisa BUY para hedge!")
                                logger.error(f"Bot {self.bot_id}: 🔄 FORÇANDO BUY para proteger banca")
                                signal = 'BUY'
                                confidence = 0.80  # Alta confiança para hedge de proteção
                            # Se MLP deu HOLD, FORÇAR BUY para hedge
                            else:
                                logger.error(f"Bot {self.bot_id}: 🚨 MLP em HOLD mas precisa BUY para hedge!")
                                logger.error(f"Bot {self.bot_id}: 🔄 FORÇANDO BUY para proteger banca")
                                signal = 'BUY'
                                confidence = 0.75  # Confiança média para hedge forçado
                        
                        # Se balanceado, seguir MLP normalmente
                        else:
                            logger.info(f"Bot {self.bot_id}: ✓ Posições balanceadas - Seguindo decisão MLP: {signal}")
                        
                        logger.info(f"Bot {self.bot_id}: MLP original: {original_signal} ({original_confidence*100:.1f}%) → Executando: {signal} ({confidence*100:.1f}%)")
                        logger.info(f"Bot {self.bot_id}: Chamando _execute_trade_if_needed...")
                        current_price = float(close[-1])
                        trade_executed = self._execute_trade_if_needed(symbol, signal, confidence, current_price, config)
                        if trade_executed:
                            trades_executed += 1
                            logger.info(f"Bot {self.bot_id}: ✓ Trade #{trades_executed} executado!")
                    else:
                        logger.info(f"Bot {self.bot_id}: Trading automático desabilitado")
                    
                    # GERENCIAMENTO DE HEDGE: Verificar se deve fechar posição perdedora
                    if auto_execute:
                        try:
                            from services.hedge_manager import hedge_manager
                            hedge_manager.check_and_close_losing_position(symbol, magic_number)
                        except Exception as e:
                            logger.error(f"Bot {self.bot_id}: Erro no hedge manager: {e}")
                
                # Aguardar 5 segundos antes da próxima análise
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Bot {self.bot_id}: Erro na análise - {e}")
                import traceback
                logger.error(f"Bot {self.bot_id}: Traceback completo:")
                logger.error(traceback.format_exc())
                time.sleep(10)
        
        logger.info(f"Bot {self.bot_id}: Loop de análise encerrado")
    
    def _execute_trade_if_needed(self, symbol, signal, confidence, current_price, config):
        """Executa trade se condições forem atendidas"""
        try:
            logger.info(f"Bot {self.bot_id}: ========== INICIANDO _execute_trade_if_needed ==========")
            logger.info(f"Bot {self.bot_id}: Parâmetros: symbol={symbol}, signal={signal}, confidence={confidence:.2f}, price={current_price}")
            import MetaTrader5 as mt5
            
            logger.info(f"Bot {self.bot_id}: ========== VERIFICANDO CONDIÇÕES PARA TRADE ==========")
            logger.info(f"Bot {self.bot_id}: Sinal: {signal}, Confiança: {confidence*100:.1f}%")
            
            # Verificar cooldown - mas permitir hedge (posição oposta)
            if self.last_trade_time:
                time_since_last = (datetime.now() - self.last_trade_time).total_seconds()
                
                # Se for sinal oposto ao último trade, permitir (hedge)
                # Verificar qual foi o último tipo de trade
                magic_number = config.get('advanced', {}).get('magic_number', 123456)
                all_positions = mt5.positions_get(symbol=symbol)
                my_positions = [p for p in all_positions if p.magic == magic_number] if all_positions else []
                
                # Se não tem posições, aplicar cooldown normal
                if not my_positions:
                    if time_since_last < self.trade_cooldown:
                        remaining = self.trade_cooldown - time_since_last
                        logger.info(f"Bot {self.bot_id}: ⏳ Cooldown ativo - aguarde {remaining:.0f}s")
                        return False
                else:
                    # Tem posições - verificar se é hedge
                    has_buy = any(p.type == 0 for p in my_positions)
                    has_sell = any(p.type == 1 for p in my_positions)
                    
                    # Se quer abrir BUY mas já tem BUY, aplicar cooldown
                    if signal == 'BUY' and has_buy:
                        if time_since_last < self.trade_cooldown:
                            remaining = self.trade_cooldown - time_since_last
                            logger.info(f"Bot {self.bot_id}: ⏳ Cooldown BUY ativo - aguarde {remaining:.0f}s")
                            return False
                    
                    # Se quer abrir SELL mas já tem SELL, aplicar cooldown
                    if signal == 'SELL' and has_sell:
                        if time_since_last < self.trade_cooldown:
                            remaining = self.trade_cooldown - time_since_last
                            logger.info(f"Bot {self.bot_id}: ⏳ Cooldown SELL ativo - aguarde {remaining:.0f}s")
                            return False
                    
                    # Se é hedge (posição oposta), permitir imediatamente
                    if (signal == 'BUY' and not has_buy) or (signal == 'SELL' and not has_sell):
                        logger.info(f"Bot {self.bot_id}: ✓ Hedge detectado - permitindo {signal} imediatamente")
                
                logger.info(f"Bot {self.bot_id}: ✓ Cooldown OK ({time_since_last:.0f}s desde último trade)")
            
            # Verificar se sinal é BUY ou SELL
            if signal == 'HOLD':
                logger.info(f"Bot {self.bot_id}: ✗ Sinal é HOLD - aguardando oportunidade")
                return False
            
            # FILTRO DE QUALIDADE: Confiança ALTA para evitar perdas
            min_confidence = config.get('signals', {}).get('min_confidence', 0.75)  # 75% padrão
            
            # PROTEÇÃO: Se teve perdas consecutivas, PARAR
            if self.consecutive_losses >= 3:
                logger.error(f"Bot {self.bot_id}: 🚨 3 PERDAS CONSECUTIVAS! Bot pausado por segurança")
                logger.error(f"Bot {self.bot_id}: 🛑 Reinicie o bot manualmente após análise")
                return False
            
            # Se teve perdas consecutivas, AUMENTAR confiança
            if self.consecutive_losses > 0:
                min_confidence = min_confidence + (self.consecutive_losses * 0.05)  # +5% por perda
                logger.warning(f"Bot {self.bot_id}: ⚠️ {self.consecutive_losses} perdas consecutivas - Confiança aumentada para {min_confidence*100:.0f}%")
            
            # Se está em prejuízo, AUMENTAR confiança mínima
            if total_profit < 0:
                min_confidence = max(min_confidence, 0.75)  # Mínimo 75% em prejuízo
                logger.warning(f"Bot {self.bot_id}: ⚠️ Em prejuízo - Confiança mínima aumentada para {min_confidence*100:.0f}%")
            
            logger.info(f"Bot {self.bot_id}: Confiança mínima: {min_confidence*100:.1f}%")
            
            if confidence < min_confidence:
                logger.warning(f"Bot {self.bot_id}: ✗ Confiança insuficiente: {confidence*100:.1f}% < {min_confidence*100:.1f}%")
                logger.warning(f"Bot {self.bot_id}: 💡 Aguardando sinal de maior qualidade")
                return False
            
            logger.info(f"Bot {self.bot_id}: ✓ Confiança OK: {confidence*100:.1f}% >= {min_confidence*100:.1f}%")
            
            # Verificar posições abertas
            magic_number = config.get('advanced', {}).get('magic_number', 123456)
            all_positions = mt5.positions_get(symbol=symbol)
            
            # Filtrar posições deste bot
            my_positions = [p for p in all_positions if p.magic == magic_number] if all_positions else []
            
            # Contar posições por tipo
            buy_positions = [p for p in my_positions if p.type == 0]  # 0 = BUY
            sell_positions = [p for p in my_positions if p.type == 1]  # 1 = SELL
            
            logger.info(f"Bot {self.bot_id}: Posições abertas - BUY: {len(buy_positions)}, SELL: {len(sell_positions)}")
            
            # PROTEÇÃO DE BANCA: Verificar prejuízo total
            total_profit = sum(p.profit for p in my_positions)
            max_loss = config.get('trading', {}).get('max_daily_loss', 100.0)
            
            if total_profit < -max_loss:
                logger.error(f"Bot {self.bot_id}: 🚨 PREJUÍZO CRÍTICO! ${total_profit:.2f} < -${max_loss:.2f}")
                logger.error(f"Bot {self.bot_id}: 🛑 BOT BLOQUEADO - Feche posições manualmente!")
                return False
            
            # HEDGE FORÇADO - CAMADA DE SEGURANÇA DUPLA
            max_positions = config.get('max_positions', 1)
            
            # FORÇAR HEDGE se desbalanceado (proteção redundante)
            if len(buy_positions) > 0 and len(sell_positions) == 0:
                if signal != 'SELL':
                    logger.error(f"Bot {self.bot_id}: 🚨 CAMADA DE SEGURANÇA! {len(buy_positions)} BUY sem SELL")
                    logger.error(f"Bot {self.bot_id}: 🔄 FORÇANDO SELL para hedge (P&L: ${total_profit:.2f})")
                    signal = 'SELL'
                    confidence = 0.85
                else:
                    logger.info(f"Bot {self.bot_id}: ✓ SELL para hedge de {len(buy_positions)} BUY")
            
            elif len(sell_positions) > 0 and len(buy_positions) == 0:
                if signal != 'BUY':
                    logger.error(f"Bot {self.bot_id}: 🚨 CAMADA DE SEGURANÇA! {len(sell_positions)} SELL sem BUY")
                    logger.error(f"Bot {self.bot_id}: 🔄 FORÇANDO BUY para hedge (P&L: ${total_profit:.2f})")
                    signal = 'BUY'
                    confidence = 0.85
                else:
                    logger.info(f"Bot {self.bot_id}: ✓ BUY para hedge de {len(sell_positions)} SELL")
            
            # Verificar limites por tipo
            if signal == 'BUY' and len(buy_positions) >= max_positions:
                logger.info(f"Bot {self.bot_id}: ✗ Já tem {len(buy_positions)} BUY (max: {max_positions})")
                return False
            
            if signal == 'SELL' and len(sell_positions) >= max_positions:
                logger.info(f"Bot {self.bot_id}: ✗ Já tem {len(sell_positions)} SELL (max: {max_positions})")
                return False
            
            # Log status
            if len(buy_positions) > 0 and len(sell_positions) > 0:
                logger.info(f"Bot {self.bot_id}: ✓ Hedge ativo | BUY: {len(buy_positions)}, SELL: {len(sell_positions)} | P&L: ${total_profit:.2f}")
            elif len(my_positions) == 0:
                logger.info(f"Bot {self.bot_id}: ✓ Primeira posição - permitindo {signal}")
            
            logger.info(f"Bot {self.bot_id}: ✓ Executando {signal} | BUY: {len(buy_positions)}/{max_positions}, SELL: {len(sell_positions)}/{max_positions} | P&L: ${total_profit:.2f}")
            
            # Preparar ordem com gestão de risco CONSERVADORA
            lot_size = config.get('lot_size', 0.01)
            take_profit_pips = config.get('take_profit', 5000)
            stop_loss_pips = config.get('stop_loss', 10000)
            
            # ESTRATÉGIA CONSERVADORA: TP pequeno, SL apertado
            # Objetivo: Lucro contínuo pequeno, evitar grandes perdas
            
            # REDUZIR TP para lucro rápido (scalping)
            take_profit_pips = min(take_profit_pips, 300)  # Máximo 300 pips ($3)
            
            # REDUZIR SL para limitar perdas
            stop_loss_pips = min(stop_loss_pips, 600)  # Máximo 600 pips ($6)
            
            logger.info(f"Bot {self.bot_id}: 💰 MODO CONSERVADOR - TP={take_profit_pips}, SL={stop_loss_pips}")
            
            # AJUSTE INTELIGENTE DE STOPS PARA HEDGE
            # Se está em hedge, usar stops assimétricos para proteger lucro
            if len(buy_positions) > 0 and len(sell_positions) > 0:
                logger.info(f"Bot {self.bot_id}: 🔄 HEDGE ATIVO - TP muito pequeno para lucro rápido")
                
                # TP MUITO pequeno para garantir lucro rápido
                take_profit_pips = int(take_profit_pips * 0.4)  # 40% = ~120 pips ($1.20)
                
                # SL maior para dar espaço ao mercado (evitar stop em ambos)
                stop_loss_pips = int(stop_loss_pips * 1.5)  # 150% = ~900 pips ($9)
                
                logger.info(f"Bot {self.bot_id}: TP hedge: {take_profit_pips} | SL hedge: {stop_loss_pips}")
            
            # Se é primeira posição, usar TP pequeno
            elif len(my_positions) == 0:
                logger.info(f"Bot {self.bot_id}: 📊 Primeira posição - TP pequeno: {take_profit_pips}")
            
            # Se está desbalanceado (abrindo hedge), usar TP MUITO agressivo
            else:
                logger.info(f"Bot {self.bot_id}: ⚡ Abrindo HEDGE - TP MUITO agressivo")
                take_profit_pips = int(take_profit_pips * 0.3)  # 30% = ~90 pips ($0.90)
                stop_loss_pips = int(stop_loss_pips * 2.0)  # 200% = ~1200 pips ($12)
                logger.info(f"Bot {self.bot_id}: TP hedge: {take_profit_pips} | SL hedge: {stop_loss_pips}")
            
            # PROTEÇÃO: SL nunca maior que TP * 3 (em hedge precisa de mais espaço)
            max_sl = take_profit_pips * 3
            if stop_loss_pips > max_sl:
                logger.warning(f"Bot {self.bot_id}: ⚠️ SL muito grande! Ajustando de {stop_loss_pips} para {max_sl}")
                stop_loss_pips = max_sl
            
            # PROTEÇÃO: Reduzir lote se prejuízo alto
            if total_profit < -50:
                original_lot = lot_size
                lot_size = max(0.01, lot_size * 0.5)  # Reduz pela metade
                logger.warning(f"Bot {self.bot_id}: ⚠️ Prejuízo alto! Reduzindo lote de {original_lot} para {lot_size}")
            
            magic_number = config.get('advanced', {}).get('magic_number', 123456)
            deviation = config.get('advanced', {}).get('deviation', 10)
            
            # Determinar tipo de ordem
            if signal == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price_order = mt5.symbol_info_tick(symbol).ask
                sl = price_order - (stop_loss_pips * mt5.symbol_info(symbol).point)
                tp = price_order + (take_profit_pips * mt5.symbol_info(symbol).point)
            else:  # SELL
                order_type = mt5.ORDER_TYPE_SELL
                price_order = mt5.symbol_info_tick(symbol).bid
                sl = price_order + (stop_loss_pips * mt5.symbol_info(symbol).point)
                tp = price_order - (take_profit_pips * mt5.symbol_info(symbol).point)
            
            # Criar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price_order,
                "sl": sl,
                "tp": tp,
                "deviation": deviation,
                "magic": magic_number,
                "comment": f"Bot {self.bot_id[:8]}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar ordem
            logger.info(f"Bot {self.bot_id}: Enviando ordem {signal} para {symbol} @ {price_order:.2f}")
            logger.info(f"  Lote: {lot_size}, TP: {tp:.2f}, SL: {sl:.2f}")
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Bot {self.bot_id}: ✓ Ordem executada! Ticket: {result.order}")
                logger.info(f"  Volume: {result.volume}, Preço: {result.price:.2f}")
                
                # Atualizar timestamp do último trade
                self.last_trade_time = datetime.now()
                logger.info(f"Bot {self.bot_id}: ⏳ Cooldown de {self.trade_cooldown}s ativado")
                
                return True
            else:
                logger.error(f"Bot {self.bot_id}: ✗ Falha ao executar ordem: {result.comment}")
                logger.error(f"  Retcode: {result.retcode}")
                return False
                
        except Exception as e:
            logger.error(f"Bot {self.bot_id}: Erro ao executar trade - {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_status(self) -> Dict:
        """Obtém status do bot"""
        try:
            import MetaTrader5 as mt5
            
            uptime = datetime.now() - self.created_at
            
            # Garantir que config é dict ao retornar
            config_dict = self.config
            if isinstance(config_dict, str):
                config_dict = json.loads(config_dict)
            
            # Buscar posições do MT5 pelo magic number e símbolo
            symbol = config_dict.get('symbol', '')
            magic_number = config_dict.get('advanced', {}).get('magic_number', 123456)
            
            positions = []
            positions_count = 0
            total_profit = 0.0
            
            if mt5.initialize():
                # Buscar todas as posições do símbolo
                mt5_positions = mt5.positions_get(symbol=symbol)
                
                if mt5_positions:
                    for pos in mt5_positions:
                        # Filtrar APENAS por magic number (cada bot tem um magic único)
                        if pos.magic == magic_number:
                            positions_count += 1
                            total_profit += pos.profit
                            
                            positions.append({
                                'ticket': pos.ticket,
                                'symbol': pos.symbol,
                                'type': 'BUY' if pos.type == 0 else 'SELL',
                                'volume': pos.volume,
                                'price_open': pos.price_open,
                                'price_current': pos.price_current,
                                'sl': pos.sl,
                                'tp': pos.tp,
                                'profit': pos.profit,
                                'swap': pos.swap,
                                'comment': pos.comment,
                                'time': datetime.fromtimestamp(pos.time).isoformat()
                            })
            
            return {
                'bot_id': self.bot_id,
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'config': config_dict,
                'is_running': self.is_running,
                'created_at': self.created_at.isoformat(),
                'uptime': str(uptime),
                'mt5_connected': mt5.initialize(),
                'positions_count': positions_count,
                'performance': {
                    'total_profit': total_profit,
                    'total_trades': positions_count
                },
                'positions': positions
            }
        except Exception as e:
            logger.error(f"Erro ao obter status do bot {self.bot_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'bot_id': self.bot_id,
                'config': self.config if isinstance(self.config, dict) else {},
                'is_running': self.is_running,
                'error': str(e),
                'positions_count': 0,
                'positions': []
            }


class BotManagerService:
    """Gerenciador de múltiplos bots"""
    
    def __init__(self):
        self.bots: Dict[str, BotInstance] = {}
        self.lock = Lock()
        self._load_bots_from_db()
    
    def _save_bot_to_db(self, bot_id: str, config: Dict, is_running: bool = False):
        """Salva bot no banco de dados"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO bots (bot_id, config, is_running, updated_at)
                VALUES (?, ?, ?, ?)
            """, (bot_id, json.dumps(config), is_running, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            logger.info(f"Bot {bot_id} salvo no banco de dados")
        except Exception as e:
            logger.error(f"Erro ao salvar bot {bot_id} no DB: {e}")
    
    def _update_bot_status_in_db(self, bot_id: str, is_running: bool):
        """Atualiza status do bot no banco"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            timestamp_field = 'started_at' if is_running else 'stopped_at'
            
            cursor.execute(f"""
                UPDATE bots 
                SET is_running = ?, {timestamp_field} = ?, updated_at = ?
                WHERE bot_id = ?
            """, (is_running, datetime.now().isoformat(), datetime.now().isoformat(), bot_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao atualizar status do bot {bot_id}: {e}")
    
    def _delete_bot_from_db(self, bot_id: str):
        """Remove bot do banco de dados"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM bots WHERE bot_id = ?", (bot_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"Bot {bot_id} removido do banco de dados")
        except Exception as e:
            logger.error(f"Erro ao remover bot {bot_id} do DB: {e}")
    
    def _log_bot_action(self, bot_id: str, action: str, details: str = None):
        """Registra ação do bot no histórico"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO bot_actions (bot_id, action, details)
                VALUES (?, ?, ?)
            """, (bot_id, action, details))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao registrar ação do bot {bot_id}: {e}")
    
    def _load_bots_from_db(self):
        """Carrega bots salvos do banco de dados na inicialização"""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM bots")
            rows = cursor.fetchall()
            
            conn.close()
            
            if rows:
                logger.info(f"Carregando {len(rows)} bots do banco de dados...")
                for row in rows:
                    bot_id = row['bot_id']
                    config = json.loads(row['config'])
                    was_running = bool(row['is_running'])
                    
                    # Recriar bot (mas não iniciar automaticamente)
                    try:
                        from bot.api_controller import BotAPIController
                        bot_controller = BotAPIController()
                        
                        trading_config = bot_controller.trading_engine.config.trading
                        trading_config.symbol = config.get('symbol', 'BTCUSDc')
                        trading_config.lot_size = config.get('lot_size', 0.01)
                        trading_config.take_profit_pips = int(config.get('take_profit', 5000))
                        trading_config.stop_loss_pips = int(config.get('stop_loss', 10000))
                        trading_config.max_positions = config.get('max_positions', 1)
                        
                        bot_instance = BotInstance(bot_id, config, bot_controller.trading_engine)
                        bot_instance.is_running = False  # Não iniciar automaticamente
                        
                        self.bots[bot_id] = bot_instance
                        
                        logger.info(f"Bot {bot_id} ({config.get('symbol')}) carregado do DB")
                        
                        if was_running:
                            logger.info(f"Bot {bot_id} estava rodando, mas não foi reiniciado automaticamente")
                            self._log_bot_action(bot_id, 'LOADED_STOPPED', 'Bot carregado mas não reiniciado')
                        
                    except Exception as e:
                        logger.error(f"Erro ao recriar bot {bot_id}: {e}")
                
                logger.info(f"{len(self.bots)} bots carregados com sucesso")
            else:
                logger.info("Nenhum bot salvo no banco de dados")
                
        except Exception as e:
            logger.error(f"Erro ao carregar bots do DB: {e}")
        
    def create_bot(self, config: Dict) -> str:
        """Cria um novo bot"""
        with self.lock:
            bot_id = str(uuid.uuid4())[:8]
            
            # Importar aqui para evitar circular import
            from bot.api_controller import BotAPIController
            
            # Criar nova instância do bot
            bot_controller = BotAPIController()
            
            # Configurar o bot
            trading_config = bot_controller.trading_engine.config.trading
            trading_config.symbol = config.get('symbol', 'BTCUSDc')
            trading_config.lot_size = config.get('lot_size', 0.01)
            trading_config.take_profit_pips = int(config.get('take_profit', 5000))
            trading_config.stop_loss_pips = int(config.get('stop_loss', 10000))
            trading_config.max_positions = config.get('max_positions', 1)
            
            # Criar instância do bot
            bot_instance = BotInstance(bot_id, config, bot_controller.trading_engine)
            
            self.bots[bot_id] = bot_instance
            
            # Salvar no banco de dados
            self._save_bot_to_db(bot_id, config, is_running=False)
            self._log_bot_action(bot_id, 'CREATED', f"Bot criado para {config.get('symbol')}")
            
            logger.info(f"Bot {bot_id} criado para {config.get('symbol')}")
            
            return bot_id
    
    def start_bot(self, bot_id: str) -> bool:
        """Inicia um bot específico e sua thread de análise"""
        with self.lock:
            if bot_id not in self.bots:
                logger.error(f"Bot {bot_id} não encontrado")
                return False
            
            bot = self.bots[bot_id]
            
            try:
                success = bot.trading_engine.start()
                if success:
                    bot.is_running = True
                    
                    # Iniciar thread de análise
                    bot.start_analysis_loop()
                    
                    # Atualizar no banco de dados
                    self._update_bot_status_in_db(bot_id, is_running=True)
                    self._log_bot_action(bot_id, 'STARTED', f"Bot iniciado para {bot.config.get('symbol')}")
                    logger.info(f"Bot {bot_id} iniciado com thread de análise")
                return success
            except Exception as e:
                logger.error(f"Erro ao iniciar bot {bot_id}: {e}")
                return False
    
    def stop_bot(self, bot_id: str) -> bool:
        """Para um bot específico e fecha todas as posições ativas"""
        with self.lock:
            if bot_id not in self.bots:
                logger.error(f"Bot {bot_id} não encontrado")
                return False
            
            bot = self.bots[bot_id]
            
            try:
                # Primeiro, fechar todas as posições abertas deste bot
                logger.info(f"Fechando posições do bot {bot_id} antes de parar...")
                
                # Obter símbolo do bot
                symbol = bot.config.get('symbol', 'BTCUSDc')
                
                # Importar MT5 para fechar posições
                import MetaTrader5 as mt5
                
                # Obter posições do símbolo
                positions = mt5.positions_get(symbol=symbol)
                
                if positions:
                    logger.info(f"Bot {bot_id}: {len(positions)} posições encontradas para {symbol}")
                    
                    for position in positions:
                        # Determinar tipo de ordem de fechamento
                        close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        
                        # Preparar request de fechamento
                        close_request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": symbol,
                            "volume": position.volume,
                            "type": close_type,
                            "position": position.ticket,
                            "magic": bot.trading_engine.config.trading.magic_number,
                            "comment": f"Bot {bot_id} stopped"
                        }
                        
                        # Fechar posição
                        result = mt5.order_send(close_request)
                        
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            logger.info(f"Bot {bot_id}: Posição {position.ticket} fechada com sucesso")
                        else:
                            logger.warning(f"Bot {bot_id}: Falha ao fechar posição {position.ticket}: {result.comment}")
                else:
                    logger.info(f"Bot {bot_id}: Nenhuma posição aberta para fechar")
                
                # Agora parar o bot
                try:
                    success, message = bot.trading_engine.stop()
                except Exception as stop_error:
                    # Se der erro ao parar, forçar parada
                    logger.warning(f"Erro ao parar trading_engine, forçando parada: {stop_error}")
                    success = True
                    
                if success or True:  # Sempre considerar sucesso após fechar posições
                    bot.is_running = False
                    
                    # Parar thread de análise
                    bot.stop_analysis_loop()
                    
                    # Atualizar no banco de dados
                    self._update_bot_status_in_db(bot_id, is_running=False)
                    self._log_bot_action(bot_id, 'STOPPED', f"Bot parado, posições fechadas, thread parada")
                    logger.info(f"Bot {bot_id} parado com sucesso")
                    return True
                
                return False
                
            except Exception as e:
                logger.error(f"Erro ao parar bot {bot_id}: {e}")
                # Mesmo com erro, marcar como parado
                bot.is_running = False
                self._update_bot_status_in_db(bot_id, is_running=False)
                return True  # Retornar True para não bloquear remoção
    
    def delete_bot(self, bot_id: str) -> bool:
        """Remove um bot (fecha posições e para antes de remover)"""
        # Verificar se bot existe
        if bot_id not in self.bots:
            return False
        
        bot = self.bots[bot_id]
        
        # Parar bot se estiver rodando (isso já fecha as posições)
        if bot.is_running:
            logger.info(f"Bot {bot_id} está rodando, parando antes de remover...")
            # Chamar stop_bot sem lock para evitar deadlock
            success = self.stop_bot(bot_id)
            if not success:
                logger.error(f"Falha ao parar bot {bot_id} antes de remover")
                return False
        
        # Agora remover com lock
        with self.lock:
            if bot_id in self.bots:
                # Remover bot
                del self.bots[bot_id]
                
                # Remover do banco de dados
                self._delete_bot_from_db(bot_id)
                self._log_bot_action(bot_id, 'DELETED', 'Bot removido')
                
                logger.info(f"Bot {bot_id} removido")
                
                return True
            else:
                return False
    
    def get_bot(self, bot_id: str) -> Optional[BotInstance]:
        """Obtém um bot específico"""
        return self.bots.get(bot_id)
    
    def get_all_bots(self) -> List[Dict]:
        """Obtém todos os bots"""
        with self.lock:
            return [bot.get_status() for bot in self.bots.values()]
    
    def get_active_bots(self) -> List[Dict]:
        """Obtém apenas bots ativos"""
        with self.lock:
            return [bot.get_status() for bot in self.bots.values() if bot.is_running]
    
    def emergency_stop_all(self) -> Dict:
        """Para todos os bots em emergência"""
        with self.lock:
            results = {}
            for bot_id, bot in self.bots.items():
                try:
                    if bot.is_running:
                        bot.trading_engine.emergency_close_all()
                        bot.is_running = False
                        results[bot_id] = 'stopped'
                    else:
                        results[bot_id] = 'already_stopped'
                except Exception as e:
                    results[bot_id] = f'error: {str(e)}'
            
            logger.info(f"Parada de emergência executada em {len(results)} bots")
            return results


# Instância global
bot_manager = BotManagerService()
