"""
Teste Rápido para Verificar Correção do Cálculo de Operações
"""

from prediction import PredictionEngine, PredictionRequest
from datetime import datetime

def test_operations_calculation():
    """Testa o cálculo correto de operações necessárias"""
    print("=" * 70)
    print("TESTE: Correção do Cálculo de Operações")
    print("=" * 70)
    
    engine = PredictionEngine()
    
    # Parâmetros do teste
    request = PredictionRequest(
        symbol="XAUUSDc",
        target_profit=30.0,
        balance=1000.0,
        timeframe="M1"
    )
    
    print(f"\n📊 PARÂMETROS DE TESTE:")
    print(f"   • Símbolo: {request.symbol}")
    print(f"   • Lucro Alvo: ${request.target_profit}")
    print(f"   • Banca: ${request.balance}")
    print(f"   • Timeframe: {request.timeframe}")
    
    try:
        print(f"\n🔄 Gerando predição...")
        result = engine.predict(request)
        
        print(f"\n✅ RESULTADOS:")
        print(f"   • Operações Estimadas: {result.estimated_operations}")
        print(f"   • Tempo Estimado: {result.estimated_duration_description}")
        print(f"   • Probabilidade: {result.success_probability * 100:.1f}%")
        
        if result.recommended_trades:
            trade = result.recommended_trades[0]
            print(f"\n🎯 RECOMENDAÇÃO PRINCIPAL:")
            print(f"   • Direção: {trade.direction}")
            print(f"   • Confiança: {trade.confidence * 100:.1f}%")
            print(f"   • Lote: {trade.lot_size}")
            print(f"   • Lucro Esperado: ${trade.expected_profit:.2f}")
            print(f"   • Perda Esperada: ${trade.expected_loss:.2f}")
            print(f"   • R/R: {trade.risk_reward_ratio:.2f}")
        
        # Cálculo manual para validação
        print(f"\n🔍 VALIDAÇÃO DO CÁLCULO:")
        if result.recommended_trades:
            lucro_por_op = trade.expected_profit
            if lucro_por_op > 0:
                ops_necessarias = request.target_profit / lucro_por_op
                print(f"   • Lucro por operação: ${lucro_por_op:.2f}")
                print(f"   • Operações necessárias (cálculo manual): {ops_necessarias:.1f}")
                print(f"   • Operações estimadas (sistema): {result.estimated_operations}")
                
                # Verificar se está próximo
                diferenca = abs(result.estimated_operations - ops_necessarias)
                if diferenca < 5:  # Margem de tolerância
                    print(f"\n   ✅ CÁLCULO CORRETO! (diferença: {diferenca:.1f})")
                else:
                    print(f"\n   ⚠️ ATENÇÃO: Grande diferença no cálculo ({diferenca:.1f} operações)")
            else:
                print(f"   ⚠️ Lucro esperado é zero ou negativo")
        
        print(f"\n💰 ESTIMATIVA DE GANHO:")
        if result.recommended_trades:
            lucro_total = trade.expected_profit * result.estimated_operations
            print(f"   • {result.estimated_operations} operações × ${trade.expected_profit:.2f}")
            print(f"   • Lucro Total Estimado: ${lucro_total:.2f}")
            print(f"   • Objetivo: ${request.target_profit}")
            
            if abs(lucro_total - request.target_profit) < 5:
                print(f"   ✅ OBJETIVO ATINGÍVEL!")
            elif lucro_total < request.target_profit:
                print(f"   ⚠️ Pode precisar de mais operações")
            else:
                print(f"   ✅ Margem de segurança positiva!")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔮 TESTE DE CORREÇÃO - MOTOR DE PREDIÇÃO")
    print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    test_operations_calculation()
    
    print("\n💡 Se o cálculo estiver correto, o número de operações deve fazer sentido")
    print("   matemático com o lucro esperado por operação.\n")
