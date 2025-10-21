"""
Teste direto: verificar se conseguimos executar ordem BTC no MT5
"""
import MetaTrader5 as mt5
from datetime import datetime

# Inicializar MT5
if not mt5.initialize():
    print("Falha ao inicializar MT5")
    exit()

symbol = "BTCUSDc"
volume = 0.01

print("="*70)
print(f"  TESTE DIRETO - {symbol}")
print("="*70)
print(f"\nHora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Selecionar símbolo
mt5.symbol_select(symbol, True)

# Obter info do símbolo
symbol_info = mt5.symbol_info(symbol)
if not symbol_info:
    print(f"✗ Símbolo {symbol} não encontrado!")
    mt5.shutdown()
    exit()

print(f"✓ Símbolo: {symbol}")
print(f"  Trade Mode: {symbol_info.trade_mode}")
print(f"  Trade Allowed: {symbol_info.trade_mode != 0}")

# Obter tick atual
tick = mt5.symbol_info_tick(symbol)
if not tick:
    print(f"✗ Falha ao obter tick de {symbol}")
    mt5.shutdown()
    exit()

print(f"\n✓ Tick Atual:")
print(f"  Bid: {tick.bid}")
print(f"  Ask: {tick.ask}")
print(f"  Time: {datetime.fromtimestamp(tick.time)}")

# Verificar se há cotação válida
if tick.bid == 0 or tick.ask == 0:
    print(f"\n✗ MERCADO FECHADO - Sem cotação válida")
    mt5.shutdown()
    exit()

print(f"\n✓ Mercado parece estar ABERTO")

# Tentar enviar ordem SEM SL/TP
print(f"\nTentando enviar ordem BUY {volume} lote...")

request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": symbol,
    "volume": volume,
    "type": mt5.ORDER_TYPE_BUY,
    "magic": 123456,
    "comment": "Teste direto BTC"
}

print(f"Request: {request}")

# Enviar ordem
result = mt5.order_send(request)

print(f"\nResultado:")
print(f"  Retcode: {result.retcode}")
print(f"  Comment: {result.comment}")

# Códigos de retorno comuns
retcode_dict = {
    10009: "TRADE_RETCODE_DONE - Sucesso",
    10013: "TRADE_RETCODE_INVALID_VOLUME",
    10014: "TRADE_RETCODE_INVALID_PRICE",
    10015: "TRADE_RETCODE_INVALID_STOPS",
    10018: "TRADE_RETCODE_MARKET_CLOSED",
    10019: "TRADE_RETCODE_NO_MONEY",
    10027: "TRADE_RETCODE_TRADE_DISABLED"
}

print(f"  Descrição: {retcode_dict.get(result.retcode, 'Código desconhecido')}")

if result.retcode == mt5.TRADE_RETCODE_DONE:
    print(f"\n✓ SUCESSO! Ordem executada!")
    print(f"  Ticket: {result.order}")
    print(f"  Volume: {result.volume}")
    print(f"  Price: {result.price}")
    
    # Fechar imediatamente
    print(f"\nFechando posição...")
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        pos = positions[0]
        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL,
            "position": pos.ticket,
            "magic": 123456,
            "comment": "Fechamento teste"
        }
        
        close_result = mt5.order_send(close_request)
        if close_result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✓ Posição fechada!")
        else:
            print(f"✗ Erro ao fechar: {close_result.comment}")
else:
    print(f"\n✗ FALHA ao executar ordem")
    
    # Diagnóstico adicional
    if result.retcode == 10018:
        print(f"\n  Diagnóstico: Mercado está fechado")
        print(f"  - Verifique se o símbolo está selecionado no Market Watch")
        print(f"  - Verifique horário de trading do símbolo")
    elif result.retcode == 10027:
        print(f"\n  Diagnóstico: Trading desabilitado")
        print(f"  - Verifique se AutoTrading está habilitado no MT5")
        print(f"  - Verifique se a conta permite trading")

# Info da conta
account_info = mt5.account_info()
if account_info:
    print(f"\nConta MT5:")
    print(f"  Servidor: {account_info.server}")
    print(f"  Balance: ${account_info.balance:.2f}")
    print(f"  Trade Allowed: {account_info.trade_allowed}")
    print(f"  Trade Expert: {account_info.trade_expert}")

mt5.shutdown()
