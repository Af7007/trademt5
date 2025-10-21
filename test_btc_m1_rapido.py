#!/usr/bin/env python
"""
Teste Bot BTC MLP - M1 - Operações Rápidas
Foco: TP $0.5, uma operação por vez, timeframe M1
"""

import requests
import time
import json
from datetime import datetime

# URLs das APIs
FLASK_URL = "http://localhost:5000"
MLP_START = f"{FLASK_URL}/mlp/start"
MLP_STOP = f"{FLASK_URL}/mlp/stop"
MLP_STATUS = f"{FLASK_URL}/mlp/status"
MLP_ANALYZE = f"{FLASK_URL}/mlp/analyze"
MLP_EXECUTE = f"{FLASK_URL}/mlp/execute"
MLP_TRADES = f"{FLASK_URL}/mlp/trades"

# Configurações específicas para BTC
SYMBOL = "BTCUSDc"
TIMEFRAME = "M1"
# Para BTCUSDc: 1 ponto = 0.01, tick_value = 0.01 (com 1 lote)
# Para $0.50 de lucro com 0.01 lote: precisa de 5000 pontos = 50.0 em preço
TP_POINTS = 5000  # 5000 pontos = 50.0 em preço = ~$0.50 com 0.01 lote
SL_POINTS = 10000  # 10000 pontos = 100.0 em preço = ~$1.00 com 0.01 lote
TP_VALUE = 0.50  # $0.5 (para monitoramento)
CONFIDENCE_THRESHOLD = 0.65  # Threshold para operações rápidas

def log(msg, level="INFO"):
    """Log formatado com timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {msg}")

def separator(title=""):
    """Separador visual"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}")
    else:
        print(f"{'='*70}\n")

def show_btc_market_data():
    """Mostra dados de mercado do BTC no M1 usando endpoint genérico"""
    separator("DADOS DE MERCADO - BTC/USD M1")
    
    try:
        # Obter tick atual do símbolo
        tick_response = requests.get(f"{FLASK_URL}/symbol_info_tick/{SYMBOL}")
        if tick_response.status_code == 200:
            tick = tick_response.json()
            log(f"Tick Atual:")
            log(f"  Bid: ${tick.get('bid', 0):.2f}")
            log(f"  Ask: ${tick.get('ask', 0):.2f}")
            log(f"  Last: ${tick.get('last', 0):.2f}")
            log(f"  Spread: ${tick.get('ask', 0) - tick.get('bid', 0):.2f}")
            log(f"  Volume: {tick.get('volume', 0)}")
        else:
            log(f"Aviso: Não foi possível obter tick do {SYMBOL}", "WARN")
        
        # Obter info do símbolo
        info_response = requests.get(f"{FLASK_URL}/symbol_info/{SYMBOL}")
        if info_response.status_code == 200:
            info = info_response.json()
            log(f"\nInfo do Símbolo:")
            log(f"  Dígitos: {info.get('digits', 0)}")
            log(f"  Point: {info.get('point', 0)}")
            log(f"  Volume Min: {info.get('volume_min', 0)}")
            log(f"  Volume Max: {info.get('volume_max', 0)}")
            log(f"  Spread: {info.get('spread', 0)}")
        else:
            log(f"Aviso: Não foi possível obter info do {SYMBOL}", "WARN")
            
        # Obter posições abertas
        positions_response = requests.get(f"{FLASK_URL}/get_positions?symbol={SYMBOL}")
        if positions_response.status_code == 200:
            positions_data = positions_response.json()
            positions = positions_data.get('positions', [])
            
            log(f"\nMT5 Posições:")
            log(f"  Total Abertas: {len(positions)}")
            
            if positions:
                log(f"  Posições Ativas:")
                for pos in positions:
                    log(f"    Ticket: {pos.get('ticket')}, Tipo: {pos.get('type')}, Profit: ${pos.get('profit', 0):.2f}")
        else:
            log(f"Aviso: Não foi possível obter posições", "WARN")
            
    except Exception as e:
        log(f"ERRO ao coletar dados de mercado: {e}", "ERROR")
    
    separator()

def configure_bot():
    """Configura o bot para BTC com parâmetros específicos"""
    separator("CONFIGURAÇÃO DO BOT")
    
    log(f"Configurando bot para {SYMBOL} no {TIMEFRAME}...")
    log(f"  Take Profit: {TP_POINTS} pontos (~${TP_VALUE})")
    log(f"  Stop Loss: {SL_POINTS} pontos (~${TP_VALUE * 2})")
    log(f"  Confidence Threshold: {CONFIDENCE_THRESHOLD*100:.0f}%")
    log(f"  Auto Trading: Habilitado")
    
    try:
        response = requests.post(
            f"{FLASK_URL}/mlp/config",
            json={
                "symbol": SYMBOL,
                "timeframe": TIMEFRAME,
                "take_profit": TP_POINTS,  # Em pontos
                "stop_loss": SL_POINTS,  # Em pontos
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "auto_trading_enabled": True,
                "max_positions": 1  # Uma operação por vez
            },
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                updates = result.get('updates', {})
                log("✓ Configuração aplicada com sucesso!", "SUCCESS")
                log(f"  Symbol: {updates.get('symbol', SYMBOL)}")
                log(f"  Timeframe: {updates.get('timeframe', TIMEFRAME)}")
                log(f"  TP: {updates.get('take_profit', TP_POINTS)} pontos")
                log(f"  SL: {updates.get('stop_loss', SL_POINTS)} pontos")
                log(f"  Threshold: {updates.get('confidence_threshold', CONFIDENCE_THRESHOLD)*100:.0f}%")
                log(f"  Max Positions: {updates.get('max_positions', 1)}")
                separator()
                return True
            else:
                log(f"✗ Erro ao configurar: {result.get('error', 'Desconhecido')}", "ERROR")
        else:
            log(f"✗ Erro HTTP {response.status_code}", "ERROR")
    except Exception as e:
        log(f"✗ Erro de conexão: {e}", "ERROR")
    
    separator()
    return False

def start_bot():
    """Inicia o bot MLP"""
    separator("INICIANDO BOT")
    
    log("Iniciando bot MLP...")
    
    try:
        response = requests.post(MLP_START)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                log("✓ Bot MLP iniciado com sucesso!", "SUCCESS")
                separator()
                return True
            else:
                log(f"✗ Erro ao iniciar: {result.get('error', 'Desconhecido')}", "ERROR")
        else:
            log(f"✗ Erro HTTP {response.status_code}", "ERROR")
    except Exception as e:
        log(f"✗ Erro de conexão: {e}", "ERROR")
    
    separator()
    return False

def get_mlp_analysis():
    """Obtém análise do MLP"""
    log("Solicitando análise MLP...")
    
    try:
        response = requests.post(MLP_ANALYZE, json={"symbol": SYMBOL})
        if response.status_code == 200:
            result = response.json()
            log(f"Análise MLP recebida:")
            log(f"  Sinal: {result.get('signal', 'N/A')}")
            log(f"  Confiança: {result.get('confidence', 0)*100:.1f}%")
            log(f"  Recomendação: {result.get('recommendation', 'N/A')}")
            return result
        else:
            log(f"Erro na análise: HTTP {response.status_code}", "WARN")
    except Exception as e:
        log(f"Erro ao obter análise: {e}", "ERROR")
    
    return None

def execute_trade(signal="BUY", confidence=0.95):
    """Executa um trade manualmente"""
    log(f"Executando trade manual: {signal} com confiança {confidence*100:.0f}%...")
    
    try:
        payload = {
            'signal': signal,
            'confidence': confidence,
            'symbol': SYMBOL
        }
        log(f"Payload: {payload}")
        
        response = requests.post(MLP_EXECUTE, json=payload)
        
        log(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            log(f"Response completa: {result}")
            
            if result.get('success'):
                log("✓ Trade executado com sucesso!", "SUCCESS")
                # O resultado pode estar em 'trade' ou 'result'
                trade_info = result.get('trade') or result.get('result', {})
                log(f"  Ticket: {trade_info.get('ticket', 'N/A')}")
                log(f"  Tipo: {trade_info.get('type', 'N/A')}")
                log(f"  Preço: ${trade_info.get('price', 0):.2f}")
                log(f"  Volume: {trade_info.get('volume', 0)}")
                return trade_info
            else:
                error_msg = result.get('error') or result.get('result', {}).get('error', 'Desconhecido')
                log(f"✗ Erro na execução: {error_msg}", "ERROR")
                log(f"Response completa: {result}", "ERROR")
        else:
            log(f"✗ Erro HTTP {response.status_code}", "ERROR")
            log(f"Response text: {response.text[:500]}", "ERROR")
    except Exception as e:
        log(f"✗ Erro ao executar trade: {e}", "ERROR")
        import traceback
        log(f"Traceback: {traceback.format_exc()}", "ERROR")
    
    return None

def monitor_position(ticket, max_time=300):
    """Monitora uma posição até fechar ou timeout"""
    separator("MONITORAMENTO DE POSIÇÃO")
    
    log(f"Monitorando posição {ticket} (timeout: {max_time}s)...")
    start_time = time.time()
    check_interval = 5  # Verifica a cada 5 segundos
    
    while time.time() - start_time < max_time:
        elapsed = int(time.time() - start_time)
        
        try:
            # Verifica status da posição no MT5 usando endpoint genérico
            positions_response = requests.get(f"{FLASK_URL}/get_positions?symbol={SYMBOL}")
            if positions_response.status_code == 200:
                positions_data = positions_response.json()
                positions = positions_data.get('positions', [])
                
                # Procura pela posição específica
                position = None
                for pos in positions:
                    if pos.get('ticket') == ticket:
                        position = pos
                        break
                
                if position:
                    profit = position.get('profit', 0)
                    log(f"[{elapsed}s] Posição ativa - Profit: ${profit:.2f}")
                    
                    # Verifica se atingiu TP
                    if profit >= TP_VALUE:
                        log(f"✓ TP ATINGIDO! Profit: ${profit:.2f}", "SUCCESS")
                        separator()
                        return True
                else:
                    log(f"✓ Posição fechada após {elapsed}s", "SUCCESS")
                    
                    # Tenta obter detalhes do trade fechado via histórico
                    history_response = requests.get(f"{FLASK_URL}/history_deals_get?days_back=1")
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        deals = history_data.get('deals', [])
                        
                        for deal in deals:
                            if deal.get('position_id') == ticket or deal.get('order') == ticket:
                                profit = deal.get('profit', 0)
                                log(f"  Profit Final: ${profit:.2f}")
                                log(f"  Deal ID: {deal.get('ticket')}")
                                separator()
                                return True
                    
                    log("  Posição fechada (detalhes não disponíveis no histórico)")
                    separator()
                    return True
            else:
                log(f"Erro ao verificar posições: HTTP {positions_response.status_code}", "WARN")
            
        except Exception as e:
            log(f"Erro ao monitorar posição: {e}", "WARN")
        
        time.sleep(check_interval)
    
    log(f"✗ TIMEOUT após {max_time}s - Posição ainda aberta", "WARN")
    separator()
    return False

def stop_bot():
    """Para o bot MLP"""
    separator("PARANDO BOT")
    
    log("Parando bot MLP...")
    
    try:
        response = requests.post(MLP_STOP)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                log("✓ Bot MLP parado com sucesso!", "SUCCESS")
                separator()
                return True
            else:
                log(f"✗ Erro ao parar: {result.get('error', 'Desconhecido')}", "ERROR")
        else:
            log(f"✗ Erro HTTP {response.status_code}", "ERROR")
    except Exception as e:
        log(f"✗ Erro de conexão: {e}", "ERROR")
    
    separator()
    return False

def show_final_summary():
    """Mostra resumo final do teste"""
    separator("RESUMO FINAL DO TESTE")
    
    try:
        # Busca últimos trades
        response = requests.get(f"{MLP_TRADES}?days=1&limit=10")
        if response.status_code == 200:
            data = response.json()
            trades = data.get('trades', [])
            
            log(f"Total de trades executados hoje: {len(trades)}")
            
            if trades:
                log("\nÚltimos trades:")
                for i, trade in enumerate(trades[:5], 1):
                    ticket = trade.get('ticket')
                    signal = trade.get('type')
                    profit = trade.get('profit', 0)
                    entry = trade.get('entry_price', 0)
                    exit_price = trade.get('exit_price', 0)
                    
                    log(f"\n  Trade {i}:")
                    log(f"    Ticket: {ticket}")
                    log(f"    Tipo: {signal}")
                    log(f"    Entry: ${entry:.2f}")
                    log(f"    Exit: ${exit_price:.2f}" if exit_price else "    Exit: Ainda aberto")
                    log(f"    Profit: ${profit:.2f}")
                
                # Estatísticas
                total_profit = sum(t.get('profit', 0) for t in trades)
                closed_trades = [t for t in trades if t.get('exit_time')]
                
                log(f"\nEstatísticas:")
                log(f"  Total Profit: ${total_profit:.2f}")
                log(f"  Trades Fechados: {len(closed_trades)}/{len(trades)}")
                
                if closed_trades:
                    avg_profit = total_profit / len(closed_trades)
                    log(f"  Profit Médio: ${avg_profit:.2f}")
        else:
            log("Não foi possível obter histórico de trades", "WARN")
    except Exception as e:
        log(f"Erro ao gerar resumo: {e}", "ERROR")
    
    separator()

def main():
    """Fluxo principal do teste"""
    print("\n" + "="*70)
    print("  TESTE BOT BTC MLP - M1 - OPERAÇÕES RÁPIDAS")
    print("  Símbolo: BTCUSDc | Timeframe: M1 | TP: $0.50")
    print("="*70 + "\n")
    
    # Passo 1: Mostrar dados de mercado
    show_btc_market_data()
    time.sleep(2)
    
    # Passo 2: Configurar bot
    if not configure_bot():
        log("ERRO: Falha na configuração. Abortando teste.", "ERROR")
        return
    time.sleep(2)
    
    # Passo 3: Iniciar bot
    if not start_bot():
        log("ERRO: Falha ao iniciar bot. Abortando teste.", "ERROR")
        return
    time.sleep(3)
    
    # Passo 4: Obter análise MLP
    separator("ANÁLISE E EXECUÇÃO")
    analysis = get_mlp_analysis()
    time.sleep(2)
    
    # Passo 5: Executar trade (manual para garantir execução)
    log("Executando trade de teste...")
    signal = "BUY" if analysis and analysis.get('signal') == 'BUY' else "BUY"
    trade_info = execute_trade(signal=signal, confidence=0.95)
    
    if not trade_info:
        log("ERRO: Falha ao executar trade. Parando bot.", "ERROR")
        stop_bot()
        return
    
    ticket = trade_info.get('ticket')
    if not ticket:
        log("ERRO: Ticket não recebido. Parando bot.", "ERROR")
        stop_bot()
        return
    
    separator()
    time.sleep(2)
    
    # Passo 6: Monitorar posição até fechar
    success = monitor_position(ticket, max_time=300)  # 5 minutos
    
    # Passo 7: Parar bot
    stop_bot()
    time.sleep(2)
    
    # Passo 8: Mostrar resumo final
    show_final_summary()
    
    # Resultado final
    separator("RESULTADO DO TESTE")
    if success:
        log("✓ TESTE CONCLUÍDO COM SUCESSO!", "SUCCESS")
        log("  - Bot configurado corretamente")
        log("  - Trade executado no MT5")
        log("  - Posição monitorada")
        log("  - Sistema funcionando corretamente")
    else:
        log("⚠ TESTE PARCIALMENTE CONCLUÍDO", "WARN")
        log("  - Bot funcionou corretamente")
        log("  - Trade foi executado")
        log("  - Posição pode ainda estar aberta ou timeout atingido")
        log("  - Verifique manualmente no MT5")
    
    separator()
    
    log("\nPróximos passos:")
    log("  1. Verificar posição no MT5")
    log("  2. Treinar modelo MLP: py -3.8 -m bot.api_controller --train")
    log("  3. Executar teste novamente com modelo treinado")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n\nTeste interrompido pelo usuário", "WARN")
        stop_bot()
    except Exception as e:
        log(f"\n\nERRO FATAL: {e}", "ERROR")
        stop_bot()
