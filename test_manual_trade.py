#!/usr/bin/env python3
"""
Script para executar operações manuais de teste no MT5
"""

import MetaTrader5 as mt5
import time
from scalping_bot import ScalpingBot

def test_manual_buy():
    """Executa uma operação BUY manual"""
    print("=== TESTE DE OPERACAO MANUAL BUY ===")

    # Inicializar MT5
    if not mt5.initialize():
        print("ERRO: Erro ao inicializar MT5")
        return False

    print("OK: MT5 inicializado com sucesso")

    # Criar bot para usar funções auxiliares
    bot = ScalpingBot(symbol="BTCUSDc", volume=0.01)

    # Obter preço atual
    tick = mt5.symbol_info_tick("BTCUSDc")
    if tick is None:
        print("ERRO: Erro ao obter preço atual")
        return False

    current_price = tick.ask
    print(f"Preco atual ASK: {current_price:.2f}")

    # Calcular SL baseado em 20% da banca
    account_info = mt5.account_info()
    if account_info is None:
        print("ERRO: Nao foi possivel obter informacoes da conta")
        return False

    account_balance = account_info.balance
    max_loss_per_trade = account_balance * 0.20  # 20% da banca

    # Para BTCUSD, calcular movimento necessario para perder 20% da banca
    loss_per_lot_per_dollar = 0.01  # $0.01 por lote por $1 de movimento
    max_price_movement_down = max_loss_per_trade / loss_per_lot_per_dollar
    sl = current_price - max_price_movement_down

    # TP fixo para garantir $0.50 de lucro
    profit_per_lot_per_dollar = 0.01  # BTCUSD: $0.01 por lote por $1 de movimento
    desired_profit = 0.50
    price_movement_needed = desired_profit / profit_per_lot_per_dollar  # $50 de movimento
    tp = current_price + price_movement_needed

    print(f"Banca atual: ${account_balance:.2f}")
    print(f"Max perda (20%): ${max_loss_per_trade:.2f}")
    print(f"Stop Loss: ${sl:.2f} (movimento: ${max_price_movement_down:.2f})")
    print(f"Take Profit: ${tp:.2f} (movimento necessario: ${price_movement_needed:.2f})")

    # Preparar ordem BUY
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "BTCUSDc",
        "volume": 0.01,  # 0.01 lote
        "type": mt5.ORDER_TYPE_BUY,
        "price": current_price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 999999,  # Magic number para operações de teste
        "comment": "TESTE MANUAL BUY - 0.01 lote",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    print("Enviando ordem BUY...")
    result = mt5.order_send(request)

    if result is None:
        print("ERRO: Falha ao enviar ordem - resultado None")
        return False

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"ERRO: Ordem falhou: {result.retcode} - {result.comment}")
        return False

    print("OK: Ordem BUY executada com sucesso!")
    print(f"Ticket: {result.order}")
    print(f"Volume: {result.volume}")
    print(f"Preco: {result.price:.2f}")

    return result.order

def test_manual_sell():
    """Executa uma operação SELL manual"""
    print("\n=== TESTE DE OPERAÇÃO MANUAL SELL ===")

    # Inicializar MT5
    if not mt5.initialize():
        print("❌ Erro ao inicializar MT5")
        return False

    print("✅ MT5 inicializado com sucesso")

    # Criar bot para usar funções auxiliares
    bot = ScalpingBot(symbol="BTCUSDc", volume=0.01)

    # Obter preço atual
    tick = mt5.symbol_info_tick("BTCUSDc")
    if tick is None:
        print("❌ Erro ao obter preço atual")
        return False

    current_price = tick.bid
    print(f"💰 Preço atual BID: {current_price:.2f}")

    # Calcular SL e TP
    sl, tp = bot.calculate_sl_tp(current_price, "SELL")
    print(f"🛑 Stop Loss: {sl:.2f}")
    print(f"🎯 Take Profit: {tp:.2f}")

    # Preparar ordem SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "BTCUSDc",
        "volume": 0.01,  # 0.01 lote
        "type": mt5.ORDER_TYPE_SELL,
        "price": current_price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 999999,  # Magic number para operações de teste
        "comment": "TESTE MANUAL SELL - 0.01 lote",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    print("📤 Enviando ordem SELL...")
    result = mt5.order_send(request)

    if result is None:
        print("❌ Falha ao enviar ordem - resultado None")
        return False

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Ordem falhou: {result.retcode} - {result.comment}")
        return False

    print("✅ Ordem SELL executada com sucesso!")
    print(f"🎫 Ticket: {result.order}")
    print(f"📊 Volume: {result.volume}")
    print(f"💵 Preço: {result.price:.2f}")

    return result.order

def monitor_positions():
    """Monitora posições abertas"""
    print("\n=== MONITORANDO POSIÇÕES ABERTAS ===")

    if not mt5.initialize():
        print("❌ Erro ao inicializar MT5")
        return

    positions = mt5.positions_get(symbol="BTCUSDc")

    if positions is None or len(positions) == 0:
        print("📭 Nenhuma posição aberta para BTCUSDc")
        return

    print(f"📊 {len(positions)} posição(ões) aberta(s):")
    total_profit = 0

    for pos in positions:
        print(f"\n🎫 Ticket: {pos.ticket}")
        print(f"📈 Tipo: {'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL'}")
        print(f"📊 Volume: {pos.volume}")
        print(f"💰 Preço de abertura: {pos.price_open:.2f}")
        print(f"💹 Preço atual: {pos.price_current:.2f}")
        print(f"🛑 Stop Loss: {pos.sl:.2f}")
        print(f"🎯 Take Profit: {pos.tp:.2f}")
        print(f"💵 Lucro/Prejuízo: {pos.profit:.2f}")
        print(f"💬 Comentário: {pos.comment}")

        total_profit += pos.profit

    print(f"\n💰 Lucro/Prejuízo Total: {total_profit:.2f}")

def close_position(ticket):
    """Fecha uma posição específica"""
    print(f"\n=== FECHANDO POSIÇÃO {ticket} ===")

    if not mt5.initialize():
        print("❌ Erro ao inicializar MT5")
        return False

    # Obter informações da posição
    position = mt5.positions_get(ticket=ticket)
    if not position or len(position) == 0:
        print(f"❌ Posição {ticket} não encontrada")
        return False

    position = position[0]

    # Determinar tipo de ordem para fechar
    close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

    # Obter preço atual
    tick = mt5.symbol_info_tick(position.symbol)
    if tick is None:
        print("❌ Erro ao obter preço atual")
        return False

    close_price = tick.bid if position.type == mt5.ORDER_TYPE_BUY else tick.ask

    print(f"Preco de fechamento: {close_price:.2f}")

    # Preparar ordem de fechamento
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": close_type,
        "position": ticket,
        "price": close_price,
        "deviation": 20,
        "magic": position.magic,
        "comment": "FECHAMENTO MANUAL DE TESTE",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    print("Enviando ordem de fechamento...")
    result = mt5.order_send(request)

    if result is None:
        print("❌ Falha ao fechar posição - resultado None")
        return False

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Falha ao fechar: {result.retcode} - {result.comment}")
        return False

    print("Posicao fechada com sucesso!")
    print(f"Lucro/Prejuizo: {position.profit:.2f}")

    return True

def wait_for_profit_target(ticket, target_profit=0.50, timeout=300):
    """
    Aguarda até que a posição atinja o lucro desejado ou timeout

    Args:
        ticket: Ticket da posição
        target_profit: Lucro desejado em dólares
        timeout: Timeout em segundos

    Returns:
        bool: True se lucro foi atingido, False se timeout
    """
    print(f"Aguardando lucro de ${target_profit} (timeout: {timeout}s)...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Obter informações da posição
            positions = mt5.positions_get(ticket=ticket)
            if not positions or len(positions) == 0:
                print("Posicao foi fechada (provavelmente por SL ou TP)")
                return True

            position = positions[0]
            current_profit = position.profit

            print(f"Lucro atual: ${current_profit:.2f} (meta: ${target_profit})")

            if current_profit >= target_profit:
                print(f"Meta de lucro atingida! (${current_profit:.2f})")
                return True

            time.sleep(1)  # Verificar a cada segundo

        except Exception as e:
            print(f"Erro ao monitorar posicao: {e}")
            time.sleep(1)

    print(f"Timeout atingido. Fechando posicao...")
    return False

def main():
    """Função principal"""
    print("INICIANDO TESTES MANUAIS DE TRADING")
    print("=" * 50)

    try:
        # Executar operação BUY
        buy_ticket = test_manual_buy()

        if buy_ticket:
            # Aguardar até atingir lucro de $0.50 ou timeout de 5 minutos
            profit_reached = wait_for_profit_target(buy_ticket, target_profit=0.50, timeout=300)

            if profit_reached:
                print("Posicao fechada com lucro!")
            else:
                print("Fechando posicao por timeout...")
                close_position(buy_ticket)

        # Aguardar um pouco
        print("\nAguardando 3 segundos...")
        time.sleep(3)

        # Executar operação SELL
        sell_ticket = test_manual_sell()

        if sell_ticket:
            print(f"\nAguardando 5 segundos antes de fechar...")
            time.sleep(5)

            # Fechar posição após 5 segundos
            close_position(sell_ticket)

        # Monitor final
        print("\n=== STATUS FINAL ===")
        monitor_positions()

    except KeyboardInterrupt:
        print("\nTeste interrompido pelo usuário")

    except Exception as e:
        print(f"\nERRO durante o teste: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Garantir que MT5 seja finalizado
        try:
            mt5.shutdown()
            print("MT5 desconectado")
        except:
            pass

if __name__ == "__main__":
    main()
