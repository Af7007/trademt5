"""
Exemplo de Uso do Módulo de Predição
Demonstra como usar o módulo programaticamente (sem API)
"""

from prediction import PredictionEngine, PredictionRequest


def exemplo_basico():
    """Exemplo básico de predição"""
    print("=" * 60)
    print("EXEMPLO 1: Predição Básica")
    print("=" * 60)
    
    # Criar motor de predição
    engine = PredictionEngine()
    
    # Criar requisição
    request = PredictionRequest(
        symbol="XAUUSDc",
        target_profit=30.0,
        balance=1000.0,
        timeframe="M1"
    )
    
    # Gerar predição
    print("\n🔄 Gerando predição...")
    result = engine.predict(request)
    
    # Exibir resultados
    print("\n✅ Predição gerada com sucesso!\n")
    print(f"📊 Operações Estimadas: {result.estimated_operations}")
    print(f"⏱️  Tempo Estimado: {result.estimated_duration_description}")
    print(f"🎯 Probabilidade de Sucesso: {result.success_probability * 100:.1f}%")
    print(f"⚠️  Nível de Risco: {result.risk_level}")
    print(f"📈 Timeframe Recomendado: {result.best_timeframe}")
    
    # Recomendações de trade
    if result.recommended_trades:
        print(f"\n🎯 Recomendações de Trade:")
        for i, trade in enumerate(result.recommended_trades, 1):
            print(f"\n  [{i}] {trade.direction} - Confiança: {trade.confidence * 100:.1f}%")
            print(f"      Entrada: {trade.entry_price:.5f}")
            print(f"      TP: {trade.take_profit:.5f}")
            print(f"      SL: {trade.stop_loss:.5f}")
            print(f"      Lote: {trade.lot_size}")
            print(f"      Lucro Esperado: ${trade.expected_profit:.2f}")
    
    # Avisos
    if result.warnings:
        print(f"\n⚠️  Avisos:")
        for warning in result.warnings:
            print(f"  • {warning}")
    
    print("\n" + "=" * 60 + "\n")


def exemplo_avancado():
    """Exemplo com parâmetros customizados"""
    print("=" * 60)
    print("EXEMPLO 2: Predição Avançada")
    print("=" * 60)
    
    engine = PredictionEngine()
    
    # Requisição com parâmetros customizados
    request = PredictionRequest(
        symbol="BTCUSDc",
        target_profit=100.0,
        balance=5000.0,
        timeframe="M15",
        lot_size=0.02,
        take_profit=150,
        stop_loss=75,
        max_operations=20,
        risk_percentage=1.5
    )
    
    print("\n🔄 Gerando predição avançada...")
    result = engine.predict(request)
    
    print("\n✅ Resultado:\n")
    
    # Análise de mercado
    print("📈 Análise de Mercado:")
    print(f"  • Tendência: {result.market_analysis.trend.get('direction', 'N/A')}")
    print(f"  • Força: {result.market_analysis.trend.get('strength', 0) * 100:.1f}%")
    print(f"  • Volatilidade: {result.market_analysis.volatility.get('level', 'N/A')}")
    print(f"  • RSI: {result.market_analysis.indicators.get('rsi', 0):.1f}")
    
    # Estratégia
    print(f"\n📋 Estratégia:")
    print(f"  {result.strategy_description}")
    
    # Condições de entrada
    print(f"\n✅ Condições de Entrada:")
    for condition in result.entry_conditions:
        print(f"  • {condition}")
    
    # Melhores horários
    print(f"\n⏰ Melhores Horários:")
    print(f"  {', '.join(result.best_entry_times)}")
    
    # Custos
    print(f"\n💰 Custos Estimados (Exness):")
    print(f"  • Spread Total: ${result.estimated_spread_cost:.2f}")
    print(f"  • Comissão: ${result.estimated_commission:.2f}")
    print(f"  • Total: ${result.estimated_total_cost:.2f}")
    
    print("\n" + "=" * 60 + "\n")


def exemplo_analise_mercado():
    """Exemplo de análise de mercado sem predição completa"""
    print("=" * 60)
    print("EXEMPLO 3: Análise de Mercado Rápida")
    print("=" * 60)
    
    engine = PredictionEngine()
    
    # Criar requisição mínima
    request = PredictionRequest(
        symbol="EURUSDc",
        target_profit=50.0,
        balance=2000.0,
        timeframe="H1"
    )
    
    print("\n🔄 Analisando mercado...")
    
    # Apenas análise de mercado
    market_analysis = engine._analyze_market(request)
    
    print("\n✅ Análise Concluída:\n")
    print(f"📊 Símbolo: {market_analysis.symbol}")
    print(f"⏱️  Timeframe: {market_analysis.timeframe}")
    
    print(f"\n📈 Tendência:")
    trend = market_analysis.trend
    print(f"  • Direção: {trend.get('direction', 'N/A')}")
    print(f"  • Força: {trend.get('strength', 0) * 100:.1f}%")
    print(f"  • Preço Atual: {trend.get('current_price', 0):.5f}")
    print(f"  • SMA 20: {trend.get('sma_20', 0):.5f}")
    print(f"  • SMA 50: {trend.get('sma_50', 0):.5f}")
    
    print(f"\n💨 Volatilidade:")
    vol = market_analysis.volatility
    print(f"  • Nível: {vol.get('level', 'N/A')}")
    print(f"  • ATR: {vol.get('atr', 0):.5f}")
    
    print(f"\n📊 Suporte e Resistência:")
    sr = market_analysis.support_resistance
    print(f"  • Resistências: {sr.get('resistance', [])}")
    print(f"  • Suportes: {sr.get('support', [])}")
    
    print(f"\n📈 Indicadores:")
    ind = market_analysis.indicators
    print(f"  • RSI: {ind.get('rsi', 0):.1f}")
    print(f"  • MACD: {ind.get('macd', 0):.4f}")
    print(f"  • MACD Signal: {ind.get('macd_signal', 0):.4f}")
    
    print("\n" + "=" * 60 + "\n")


def exemplo_comparacao_timeframes():
    """Compara predições em diferentes timeframes"""
    print("=" * 60)
    print("EXEMPLO 4: Comparação de Timeframes")
    print("=" * 60)
    
    engine = PredictionEngine()
    timeframes = ["M1", "M5", "M15", "H1"]
    
    print("\n🔄 Comparando predições em diferentes timeframes...\n")
    
    results = {}
    
    for tf in timeframes:
        request = PredictionRequest(
            symbol="XAUUSDc",
            target_profit=50.0,
            balance=2000.0,
            timeframe=tf
        )
        
        try:
            result = engine.predict(request)
            results[tf] = {
                'operations': result.estimated_operations,
                'duration': result.estimated_duration_hours,
                'probability': result.success_probability,
                'risk': result.risk_level
            }
            print(f"✅ {tf}: {result.estimated_operations} ops em {result.estimated_duration_description}")
        except Exception as e:
            print(f"❌ {tf}: Erro - {e}")
    
    # Encontrar melhor opção
    if results:
        best_tf = max(results.items(), key=lambda x: x[1]['probability'])
        print(f"\n🏆 Melhor Timeframe: {best_tf[0]}")
        print(f"   Probabilidade: {best_tf[1]['probability'] * 100:.1f}%")
        print(f"   Operações: {best_tf[1]['operations']}")
        print(f"   Duração: {best_tf[1]['duration']:.1f} horas")
    
    print("\n" + "=" * 60 + "\n")


def exemplo_multiplos_simbolos():
    """Compara predições para diferentes símbolos"""
    print("=" * 60)
    print("EXEMPLO 5: Comparação de Símbolos")
    print("=" * 60)
    
    engine = PredictionEngine()
    symbols = ["XAUUSDc", "BTCUSDc", "EURUSDc"]
    
    print("\n🔄 Analisando múltiplos símbolos...\n")
    
    for symbol in symbols:
        try:
            request = PredictionRequest(
                symbol=symbol,
                target_profit=50.0,
                balance=2000.0,
                timeframe="M5"
            )
            
            result = engine.predict(request)
            
            print(f"\n📊 {symbol}:")
            print(f"   • Operações: {result.estimated_operations}")
            print(f"   • Probabilidade: {result.success_probability * 100:.1f}%")
            print(f"   • Risco: {result.risk_level}")
            
            if result.recommended_trades:
                trade = result.recommended_trades[0]
                print(f"   • Recomendação: {trade.direction} (confiança {trade.confidence * 100:.1f}%)")
        
        except Exception as e:
            print(f"\n❌ {symbol}: Erro - {str(e)[:50]}")
    
    print("\n" + "=" * 60 + "\n")


def main():
    """Executa todos os exemplos"""
    print("\n")
    print("🔮" * 30)
    print("   EXEMPLOS DE USO - MOTOR DE PREDIÇÃO")
    print("🔮" * 30)
    print("\nDemonstração de como usar o módulo programaticamente\n")
    
    try:
        # Exemplo 1: Básico
        exemplo_basico()
        
        # Exemplo 2: Avançado
        exemplo_avancado()
        
        # Exemplo 3: Apenas análise
        exemplo_analise_mercado()
        
        # Exemplo 4: Comparação de timeframes
        exemplo_comparacao_timeframes()
        
        # Exemplo 5: Múltiplos símbolos
        exemplo_multiplos_simbolos()
        
        print("=" * 60)
        print("✅ TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Execução interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
