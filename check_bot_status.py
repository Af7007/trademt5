"""
Script para verificar por que o bot não está executando operações
"""

import requests
import json

def check_bot_status():
    """Verifica status detalhado dos bots"""
    
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DE BOT - Por que não executa?")
    print("=" * 60)
    
    try:
        # Listar bots
        response = requests.get('http://localhost:5000/bots')
        data = response.json()
        
        if not data.get('success'):
            print("❌ Erro ao listar bots")
            return
        
        bots = data.get('bots', [])
        
        if not bots:
            print("\n❌ NENHUM BOT ATIVO!")
            print("   Crie um bot primeiro")
            return
        
        print(f"\n✓ Encontrados {len(bots)} bot(s)\n")
        
        for bot in bots:
            bot_id = bot.get('bot_id')
            symbol = bot.get('symbol')
            is_running = bot.get('is_running')
            
            print("-" * 60)
            print(f"🤖 Bot: {bot_id}")
            print(f"   Símbolo: {symbol}")
            print(f"   Status: {'✓ Rodando' if is_running else '❌ Parado'}")
            
            # Verificar configuração
            config = bot.get('config', {})
            trading = config.get('trading', {})
            
            print(f"\n📋 Configuração:")
            print(f"   auto_execute: {trading.get('auto_execute', False)}")
            print(f"   max_daily_trades: {trading.get('max_daily_trades', 0)}")
            print(f"   max_daily_loss: ${trading.get('max_daily_loss', 0)}")
            print(f"   trade_cooldown: {trading.get('trade_cooldown', 0)}s")
            
            signals = config.get('signals', {})
            print(f"\n🎯 Sinais:")
            print(f"   min_confidence: {signals.get('min_confidence', 0)*100:.0f}%")
            
            # Verificar análises
            try:
                analysis_response = requests.get(f'http://localhost:5000/bots/{bot_id}/analysis?limit=5')
                analysis_data = analysis_response.json()
                
                if analysis_data.get('success'):
                    analyses = analysis_data.get('analyses', [])
                    print(f"\n📊 Últimas {len(analyses)} análises:")
                    
                    for a in analyses:
                        signal = a.get('signal')
                        confidence = a.get('confidence', 0) * 100
                        timestamp = a.get('timestamp', '')
                        print(f"   {timestamp}: {signal} ({confidence:.1f}%)")
                else:
                    print("\n⚠️ Sem análises registradas")
            except:
                print("\n⚠️ Erro ao buscar análises")
            
            # DIAGNÓSTICO
            print(f"\n🔍 DIAGNÓSTICO:")
            
            if not is_running:
                print("   ❌ BOT PARADO - Inicie o bot primeiro!")
            else:
                print("   ✓ Bot está rodando")
            
            if not trading.get('auto_execute'):
                print("   ❌ AUTO_EXECUTE DESABILITADO!")
                print("      Configure 'trading.auto_execute': true")
            else:
                print("   ✓ Auto execute habilitado")
            
            min_conf = signals.get('min_confidence', 0.65)
            if min_conf > 0.75:
                print(f"   ⚠️ Confiança mínima ALTA ({min_conf*100:.0f}%)")
                print("      Pode estar bloqueando trades")
            else:
                print(f"   ✓ Confiança mínima OK ({min_conf*100:.0f}%)")
            
            print()
        
        print("=" * 60)
        print("\n💡 SOLUÇÕES:")
        print("1. Se bot parado: Clique 'Start' no painel")
        print("2. Se auto_execute false: Edite config e ative")
        print("3. Se confiança alta: Reduza para 65-70%")
        print("4. Verifique logs em tempo real no painel")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\n⚠️ Certifique-se que o servidor está rodando:")
        print("   python app.py")


if __name__ == "__main__":
    check_bot_status()
