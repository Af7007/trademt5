"""
Testa se o MLP está gerando sinais
"""

import MetaTrader5 as mt5
from services.mlp_predictor import mlp_predictor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mlp_signals():
    """Testa geração de sinais do MLP"""
    
    print("=" * 60)
    print("🧪 TESTE DE SINAIS MLP")
    print("=" * 60)
    
    # Conectar MT5
    if not mt5.initialize():
        print("❌ Erro ao conectar MT5")
        return
    
    symbol = "XAUUSDc"
    timeframe = mt5.TIMEFRAME_M1
    
    print(f"\n📊 Testando {symbol} M1...")
    
    # Pegar dados
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    
    if rates is None or len(rates) == 0:
        print(f"❌ Erro ao obter dados de {symbol}")
        return
    
    print(f"✓ Obtidos {len(rates)} candles")
    
    # Verificar se MLP está treinado
    print(f"\n🤖 Verificando MLP...")
    
    try:
        # Tentar prever
        signal, confidence = mlp_predictor.predict(symbol, timeframe)
        
        print(f"\n✅ MLP FUNCIONANDO!")
        print(f"   Sinal: {signal}")
        print(f"   Confiança: {confidence*100:.1f}%")
        
        if signal == 'HOLD':
            print(f"\n⚠️ MLP está em HOLD")
            print(f"   Isso é normal, aguarde sinal BUY ou SELL")
        elif confidence < 0.75:
            print(f"\n⚠️ Confiança baixa: {confidence*100:.1f}%")
            print(f"   Mínimo configurado: 75%")
            print(f"   Reduza min_confidence para 65% ou aguarde")
        else:
            print(f"\n✅ SINAL VÁLIDO PARA TRADE!")
            print(f"   {signal} com {confidence*100:.1f}% confiança")
        
        # Testar várias vezes
        print(f"\n📊 Testando 5 previsões consecutivas...")
        for i in range(5):
            signal, confidence = mlp_predictor.predict(symbol, timeframe)
            print(f"   {i+1}. {signal} ({confidence*100:.1f}%)")
        
    except Exception as e:
        print(f"\n❌ ERRO NO MLP: {e}")
        print(f"\n💡 SOLUÇÃO:")
        print(f"   1. Treine o MLP primeiro:")
        print(f"      Clique 'Retreinar MLP' no painel")
        print(f"   2. Ou execute:")
        print(f"      python test_xau_m1_rapido.py")
        import traceback
        print(f"\n{traceback.format_exc()}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_mlp_signals()
