"""
Script de correção automática - Faz o bot executar operações
"""

import requests
import json
import time
import MetaTrader5 as mt5

def fix_bot():
    """Corrige configuração e força execução"""
    
    print("=" * 70)
    print("🔧 CORREÇÃO AUTOMÁTICA - FORÇAR EXECUÇÃO DE OPERAÇÕES")
    print("=" * 70)
    
    base_url = "http://localhost:5000"
    
    # 1. Verificar bots existentes
    print("\n1️⃣ Verificando bots existentes...")
    try:
        response = requests.get(f"{base_url}/bots")
        data = response.json()
        bots = data.get('bots', [])
        
        if bots:
            print(f"   ✓ Encontrados {len(bots)} bot(s)")
            
            # Parar todos os bots
            for bot in bots:
                bot_id = bot.get('bot_id')
                print(f"   🛑 Parando bot {bot_id}...")
                requests.post(f"{base_url}/bots/{bot_id}/stop")
                time.sleep(1)
        else:
            print("   ℹ️ Nenhum bot existente")
    except Exception as e:
        print(f"   ⚠️ Erro: {e}")
    
    # 2. Treinar MLP
    print("\n2️⃣ Treinando MLP para XAUUSDc...")
    try:
        if not mt5.initialize():
            print("   ❌ Erro ao conectar MT5")
            return
        
        from services.mlp_predictor import mlp_predictor
        
        print("   ⏳ Treinando... (30-60s)")
        success = mlp_predictor.train_model("XAUUSDc", mt5.TIMEFRAME_M1, num_samples=500)
        
        if success:
            print("   ✓ MLP treinado com sucesso!")
        else:
            print("   ⚠️ Falha no treinamento")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    # 3. Criar bot com configuração correta
    print("\n3️⃣ Criando bot com configuração otimizada...")
    
    config = {
        "symbol": "XAUUSDc",
        "timeframe": "M1",
        "lot_size": 0.01,
        "take_profit": 200,
        "stop_loss": 400,
        "max_positions": 1,
        "analysis_method": {
            "use_indicators": False,
            "use_mlp": True
        },
        "signals": {
            "min_confidence": 0.60
        },
        "trading": {
            "enabled": True,
            "auto_execute": True,
            "max_daily_trades": 50,
            "max_daily_loss": 50.0,
            "trade_cooldown": 5
        },
        "advanced": {
            "magic_number": 999001,
            "comment": "Bot Auto-Fix",
            "deviation": 10
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/bots",
            json={"config": config, "start": True}
        )
        result = response.json()
        
        if result.get('success'):
            bot_id = result.get('bot_id')
            print(f"   ✓ Bot criado: {bot_id}")
            print(f"   ✓ Bot iniciado automaticamente")
            
            # 4. Monitorar por 30 segundos
            print("\n4️⃣ Monitorando execução (30s)...")
            print("   " + "-" * 66)
            
            for i in range(6):
                time.sleep(5)
                
                # Verificar análises
                try:
                    analysis_response = requests.get(f"{base_url}/bots/{bot_id}/analysis?limit=1")
                    analysis_data = analysis_response.json()
                    
                    if analysis_data.get('success'):
                        analyses = analysis_data.get('analyses', [])
                        if analyses:
                            a = analyses[0]
                            signal = a.get('signal')
                            confidence = a.get('confidence', 0) * 100
                            timestamp = a.get('timestamp', '')
                            
                            print(f"   [{i+1}/6] {timestamp}: {signal} ({confidence:.1f}%)")
                            
                            if signal != 'HOLD' and confidence >= 60:
                                print(f"   ✅ SINAL VÁLIDO DETECTADO!")
                        else:
                            print(f"   [{i+1}/6] Aguardando análise...")
                    else:
                        print(f"   [{i+1}/6] Sem dados...")
                except:
                    print(f"   [{i+1}/6] Erro ao verificar...")
            
            # 5. Verificar se executou
            print("\n5️⃣ Verificando execução de trades...")
            try:
                bot_response = requests.get(f"{base_url}/bots/{bot_id}")
                bot_data = bot_response.json()
                
                if bot_data.get('success'):
                    bot_info = bot_data.get('bot')
                    positions = bot_info.get('positions', [])
                    
                    if positions:
                        print(f"   ✅ BOT EXECUTOU {len(positions)} POSIÇÃO(ÕES)!")
                        for pos in positions:
                            print(f"      • {pos['type']} @ {pos['price_open']:.2f} | P&L: ${pos['profit']:.2f}")
                    else:
                        print(f"   ⚠️ Nenhuma posição aberta ainda")
                        print(f"   💡 Aguarde mais tempo ou verifique:")
                        print(f"      - MLP pode estar gerando HOLD")
                        print(f"      - Confiança pode estar < 60%")
                        print(f"      - Mercado pode estar sem movimento")
            except Exception as e:
                print(f"   ❌ Erro: {e}")
            
            print("\n" + "=" * 70)
            print("📊 RESUMO")
            print("=" * 70)
            print(f"✓ Bot ID: {bot_id}")
            print(f"✓ Símbolo: XAUUSDc M1")
            print(f"✓ MLP: Habilitado")
            print(f"✓ Auto Execute: Habilitado")
            print(f"✓ Confiança Mínima: 60%")
            print(f"✓ TP: 200 pips ($2.00)")
            print(f"✓ SL: 400 pips ($4.00)")
            print("\n💡 Acesse: http://localhost:5000/bot-manager-pro")
            print("   Veja logs em tempo real")
            print("=" * 70)
            
        else:
            print(f"   ❌ Erro ao criar bot: {result.get('error')}")
    except Exception as e:
        print(f"   ❌ Erro: {e}")


if __name__ == "__main__":
    print("\n⚠️  Este script vai:")
    print("   1. Parar bots existentes")
    print("   2. Treinar MLP")
    print("   3. Criar novo bot otimizado")
    print("   4. Monitorar execução\n")
    
    confirm = input("Continuar? (S/N): ")
    
    if confirm.upper() == 'S':
        fix_bot()
    else:
        print("❌ Cancelado")
