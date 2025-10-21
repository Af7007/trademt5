"""
Script de Emergência - Fecha TODAS as posições
Use quando o bot estiver quebrando a banca
"""

import MetaTrader5 as mt5
from datetime import datetime

def emergency_close_all():
    """Fecha todas as posições abertas IMEDIATAMENTE"""
    
    print("=" * 60)
    print("🚨 EMERGÊNCIA - FECHANDO TODAS AS POSIÇÕES")
    print("=" * 60)
    
    # Conectar MT5
    if not mt5.initialize():
        print("❌ Erro ao conectar MT5")
        return False
    
    # Pegar todas as posições
    positions = mt5.positions_get()
    
    if not positions:
        print("✓ Nenhuma posição aberta")
        return True
    
    print(f"\n📊 Encontradas {len(positions)} posições abertas")
    print("-" * 60)
    
    closed_count = 0
    failed_count = 0
    total_profit = 0
    
    for pos in positions:
        symbol = pos.symbol
        ticket = pos.ticket
        volume = pos.volume
        pos_type = "BUY" if pos.type == 0 else "SELL"
        profit = pos.profit
        total_profit += profit
        
        print(f"\n🔄 Fechando: {symbol} | {pos_type} | Lote: {volume} | P&L: ${profit:.2f}")
        
        # Determinar tipo de fechamento
        if pos.type == 0:  # BUY
            close_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:  # SELL
            close_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask
        
        # Criar request de fechamento
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": pos.magic,
            "comment": "EMERGÊNCIA - Fechamento",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Enviar ordem
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   ✓ Fechado! Ticket: {result.order}")
            closed_count += 1
        else:
            print(f"   ✗ Falha: {result.comment} (Retcode: {result.retcode})")
            failed_count += 1
    
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    print(f"✓ Fechadas: {closed_count}")
    print(f"✗ Falharam: {failed_count}")
    print(f"💰 P&L Total: ${total_profit:.2f}")
    print("=" * 60)
    
    return closed_count > 0


if __name__ == "__main__":
    print("\n⚠️  ATENÇÃO: Este script fecha TODAS as posições abertas!")
    print("⚠️  Use apenas em EMERGÊNCIA quando o bot estiver quebrando a banca!\n")
    
    confirm = input("Digite 'SIM' para confirmar: ")
    
    if confirm.upper() == "SIM":
        emergency_close_all()
    else:
        print("❌ Cancelado")
