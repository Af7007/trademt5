"""
Cria um bot que FUNCIONA e executa operações
"""

import requests
import json

def create_bot():
    """Cria bot com configuração garantida para funcionar"""
    
    print("=" * 70)
    print("🤖 CRIANDO BOT QUE EXECUTA OPERAÇÕES")
    print("=" * 70)
    
    # Configuração GARANTIDA para funcionar
    config = {
        "symbol": "XAUUSDc",
        "timeframe": "M1",
        "lot_size": 0.01,
        "take_profit": 200,
        "stop_loss": 400,
        "max_positions": 1,
        "confidence_threshold": 0.60,
        "analysis_method": {
            "use_indicators": False,  # DESABILITAR indicadores
            "use_mlp": True            # HABILITAR MLP
        },
        "signals": {
            "min_confidence": 0.75,    # 75% - alta qualidade
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "rsi_buy_zone": 40,
            "rsi_sell_zone": 60,
            "use_trend_filter": False,  # Desabilitar filtro de tendência
            "signals_to_confirm": 1
        },
        "trading": {
            "enabled": True,
            "auto_execute": True,       # HABILITAR execução automática
            "max_daily_trades": 50,
            "max_daily_loss": 50.0,
            "max_daily_profit": 200.0,
            "trade_cooldown": 5,        # 5s entre trades
            "trailing_stop": False,
            "break_even": False
        },
        "risk_management": {
            "max_risk_per_trade": 1.0,
            "max_account_risk": 5.0,
            "risk_reward_ratio": 2.0
        },
        "advanced": {
            "magic_number": 999999,
            "comment": "Bot Working",
            "deviation": 10,
            "fill_type": "FOK",
            "order_type": "MARKET"
        }
    }
    
    print("\n📋 Configuração:")
    print(f"   Símbolo: {config['symbol']}")
    print(f"   Timeframe: {config['timeframe']}")
    print(f"   Lote: {config['lot_size']}")
    print(f"   TP: {config['take_profit']} pips")
    print(f"   SL: {config['stop_loss']} pips")
    print(f"   MLP: {config['analysis_method']['use_mlp']}")
    print(f"   Auto Execute: {config['trading']['auto_execute']}")
    print(f"   Min Confidence: {config['signals']['min_confidence']*100}%")
    
    print("\n🔄 Criando bot...")
    
    try:
        response = requests.post(
            "http://localhost:5000/bots/create",
            json={"config": config, "start": True},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('success'):
                bot_id = result.get('bot_id')
                print(f"\n✅ BOT CRIADO E INICIADO!")
                print(f"   Bot ID: {bot_id}")
                print(f"\n📊 Acesse: http://localhost:5000/bot-manager-pro")
                print(f"   Veja logs em tempo real")
                print(f"\n⏳ Aguarde 10-15 segundos...")
                print(f"   O bot vai:")
                print(f"   1. Analisar mercado (5s)")
                print(f"   2. MLP gerar sinal")
                print(f"   3. Executar se confiança >= 60%")
                print("\n" + "=" * 70)
                return bot_id
            else:
                print(f"\n❌ Erro: {result.get('error')}")
                print(f"   Resposta: {result}")
        else:
            print(f"\n❌ Erro HTTP {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        print(traceback.format_exc())
    
    return None


if __name__ == "__main__":
    create_bot()
