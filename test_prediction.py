"""
Script de teste para o Motor de Predição
Demonstra como usar o módulo de predição
"""

import requests
import json
from datetime import datetime


def test_basic_prediction():
    """Teste básico de predição"""
    print("=" * 60)
    print("TESTE 1: Predição Básica para XAUUSDc")
    print("=" * 60)
    
    url = "http://localhost:5000/prediction/analyze"
    data = {
        "symbol": "XAUUSDc",
        "target_profit": 30.0,
        "balance": 1000.0,
        "timeframe": "M1"
    }
    
    print(f"\n📤 Enviando requisição...")
    print(f"Símbolo: {data['symbol']}")
    print(f"Lucro Alvo: ${data['target_profit']}")
    print(f"Banca: ${data['balance']}")
    print(f"Timeframe: {data['timeframe']}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        result = response.json()
        
        if result.get('success'):
            print("\n✅ Predição gerada com sucesso!\n")
            display_prediction_summary(result['result'])
        else:
            print(f"\n❌ Erro: {result.get('error')}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
        print("Certifique-se que o servidor Flask está rodando na porta 5000")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


def test_advanced_prediction():
    """Teste com parâmetros avançados"""
    print("\n" + "=" * 60)
    print("TESTE 2: Predição Avançada com Parâmetros Customizados")
    print("=" * 60)
    
    url = "http://localhost:5000/prediction/analyze"
    data = {
        "symbol": "XAUUSDc",
        "target_profit": 50.0,
        "balance": 2000.0,
        "timeframe": "M5",
        "lot_size": 0.02,
        "take_profit": 150,
        "stop_loss": 75,
        "max_operations": 20,
        "risk_percentage": 1.5
    }
    
    print(f"\n📤 Enviando requisição avançada...")
    print(f"Símbolo: {data['symbol']}")
    print(f"Lucro Alvo: ${data['target_profit']}")
    print(f"Banca: ${data['balance']}")
    print(f"Lote: {data['lot_size']}")
    print(f"TP: {data['take_profit']} pontos")
    print(f"SL: {data['stop_loss']} pontos")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        result = response.json()
        
        if result.get('success'):
            print("\n✅ Predição gerada com sucesso!\n")
            display_prediction_summary(result['result'])
        else:
            print(f"\n❌ Erro: {result.get('error')}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


def test_quick_prediction():
    """Teste de predição rápida"""
    print("\n" + "=" * 60)
    print("TESTE 3: Predição Rápida")
    print("=" * 60)
    
    url = "http://localhost:5000/prediction/quick-prediction"
    data = {
        "symbol": "BTCUSDc",
        "target_profit": 100.0,
        "balance": 5000.0
    }
    
    print(f"\n📤 Enviando predição rápida...")
    print(f"Símbolo: {data['symbol']}")
    print(f"Lucro Alvo: ${data['target_profit']}")
    
    try:
        response = requests.post(url, json=data, timeout=30)
        result = response.json()
        
        if result.get('success'):
            print("\n✅ Predição rápida gerada!\n")
            summary = result.get('summary', {})
            
            print("📊 RESUMO RÁPIDO:")
            print(f"  • Operações: {summary.get('estimated_operations')}")
            print(f"  • Duração: {summary.get('estimated_duration')}")
            print(f"  • Probabilidade: {summary.get('success_probability')}")
            print(f"  • Risco: {summary.get('risk_level')}")
            print(f"  • Timeframe: {summary.get('best_timeframe')}")
            print(f"  • Lote Recomendado: {summary.get('recommended_lot_size')}")
        else:
            print(f"\n❌ Erro: {result.get('error')}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


def test_market_analysis():
    """Teste de análise de mercado"""
    print("\n" + "=" * 60)
    print("TESTE 4: Análise de Mercado")
    print("=" * 60)
    
    symbol = "XAUUSDc"
    url = f"http://localhost:5000/prediction/market-analysis/{symbol}?timeframe=M1"
    
    print(f"\n📤 Solicitando análise de mercado para {symbol}...")
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get('success'):
            print("\n✅ Análise de mercado obtida!\n")
            analysis = result.get('analysis', {})
            
            print("📈 ANÁLISE DE MERCADO:")
            
            # Tendência
            trend = analysis.get('trend', {})
            print(f"\n  Tendência:")
            print(f"    • Direção: {trend.get('direction', 'N/A')}")
            print(f"    • Força: {trend.get('strength', 0) * 100:.1f}%")
            
            # Volatilidade
            volatility = analysis.get('volatility', {})
            print(f"\n  Volatilidade:")
            print(f"    • Nível: {volatility.get('level', 'N/A')}")
            print(f"    • ATR: {volatility.get('atr', 0):.2f}")
            
            # Indicadores
            indicators = analysis.get('indicators', {})
            print(f"\n  Indicadores:")
            print(f"    • RSI: {indicators.get('rsi', 0):.1f}")
            print(f"    • MACD: {indicators.get('macd', 0):.2f}")
            print(f"    • Preço Atual: {indicators.get('current_price', 0):.2f}")
        else:
            print(f"\n❌ Erro: {result.get('error')}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


def display_prediction_summary(result):
    """Exibe resumo formatado da predição"""
    predictions = result.get('predictions', {})
    risk = result.get('risk_management', {})
    timing = result.get('timing', {})
    
    print("📊 RESUMO DA PREDIÇÃO:")
    print(f"  • Operações Estimadas: {predictions.get('estimated_operations')}")
    print(f"  • Tempo Estimado: {predictions.get('estimated_duration_description')}")
    print(f"  • Probabilidade de Sucesso: {predictions.get('success_probability', 0) * 100:.1f}%")
    print(f"  • Nível de Risco: {risk.get('risk_level')}")
    print(f"  • Timeframe Recomendado: {timing.get('best_timeframe')}")
    
    # Recomendações de trade
    trades = result.get('recommended_trades', [])
    if trades:
        print(f"\n🎯 RECOMENDAÇÕES DE TRADE ({len(trades)}):")
        for i, trade in enumerate(trades, 1):
            print(f"\n  [{i}] {trade.get('direction')} - Confiança: {trade.get('confidence', 0) * 100:.1f}%")
            print(f"      Entrada: {trade.get('entry_price'):.5f}")
            print(f"      TP: {trade.get('take_profit'):.5f}")
            print(f"      SL: {trade.get('stop_loss'):.5f}")
            print(f"      Lote: {trade.get('lot_size')}")
            print(f"      Lucro Esperado: ${trade.get('expected_profit'):.2f}")
            print(f"      Razão R/R: {trade.get('risk_reward_ratio'):.2f}")
            print(f"      Motivo: {trade.get('reasoning', 'N/A')[:100]}...")
    
    # Avisos
    warnings = result.get('warnings', [])
    if warnings:
        print(f"\n⚠️  AVISOS:")
        for warning in warnings:
            print(f"  • {warning}")
    
    # Recomendações
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMENDAÇÕES:")
        for rec in recommendations[:5]:  # Mostrar apenas 5
            print(f"  • {rec}")


def test_symbol_info():
    """Teste de informações do símbolo"""
    print("\n" + "=" * 60)
    print("TESTE 5: Informações do Símbolo")
    print("=" * 60)
    
    symbol = "XAUUSDc"
    url = f"http://localhost:5000/prediction/symbol-info/{symbol}"
    
    print(f"\n📤 Solicitando informações de {symbol}...")
    
    try:
        response = requests.get(url, timeout=30)
        result = response.json()
        
        if result.get('success'):
            print("\n✅ Informações obtidas!\n")
            info = result.get('symbol_info', {})
            
            print(f"📋 INFORMAÇÕES DO SÍMBOLO:")
            print(f"  • Nome: {info.get('name')}")
            print(f"  • Descrição: {info.get('description')}")
            print(f"  • Spread: {info.get('spread')} pontos")
            print(f"  • Bid: {info.get('bid'):.5f}")
            print(f"  • Ask: {info.get('ask'):.5f}")
            print(f"  • Lote Mín: {info.get('volume_min')}")
            print(f"  • Lote Máx: {info.get('volume_max')}")
            print(f"  • Dígitos: {info.get('digits')}")
        else:
            print(f"\n❌ Erro: {result.get('error')}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor.")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


def main():
    """Executa todos os testes"""
    print("\n")
    print("🔮" * 30)
    print("   TESTES DO MOTOR DE PREDIÇÃO - MT5")
    print("🔮" * 30)
    print(f"\nIniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar se servidor está online
    try:
        response = requests.get("http://localhost:5000/prediction/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor online e funcionando!\n")
        else:
            print("⚠️ Servidor respondeu mas pode estar com problemas\n")
    except:
        print("❌ ERRO: Servidor não está respondendo!")
        print("Por favor, inicie o servidor Flask antes de executar os testes.")
        print("Comando: python app.py\n")
        return
    
    # Executar testes
    tests = [
        ("Predição Básica", test_basic_prediction),
        ("Predição Avançada", test_advanced_prediction),
        ("Predição Rápida", test_quick_prediction),
        ("Análise de Mercado", test_market_analysis),
        ("Informações do Símbolo", test_symbol_info)
    ]
    
    for name, test_func in tests:
        try:
            test_func()
        except KeyboardInterrupt:
            print("\n\n❌ Testes interrompidos pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro no teste '{name}': {e}")
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)
    print(f"\nFinalizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 Dica: Acesse http://localhost:5000/prediction/dashboard para a interface gráfica")
    print("\n")


if __name__ == "__main__":
    main()
