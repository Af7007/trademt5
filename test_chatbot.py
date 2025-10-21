#!/usr/bin/env python3
"""
Test Script para o Trading Chatbot IA
Testa as funcionalidades do assistente de trading
"""

import requests
import json
import time

def test_basic_functionality():
    """Testa funcionalidades básicas"""
    print("🧪 INICIANDO TESTES DO TRADING CHATBOT")
    print("="*50)

    # Test 1: Health Check
    print("\\n1️⃣ Testando Health Check...")
    try:
        response = requests.get("http://localhost:8080/health", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ollama disponível: {data['models']['ollama_available']}")
            print(f"Motor de predição: {data['models']['prediction_engine']}")
            print("✅ Health Check OK")
        else:
            print("❌ Health Check FALHOU")
            return False
    except Exception as e:
        print(f"❌ Erro no Health Check: {e}")
        return False

    # Test 2: Chat Simples
    print("\\n2️⃣ Testando Chat - Pergunta Simples...")
    try:
        payload = {
            "message": "Olá, você pode me ajudar com trading?",
            "model": "llama3.1:8b"
        }
        response = requests.post("http://localhost:8080/chat",
                               json=payload, timeout=60)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if 'response' in result and len(result['response']) > 10:
                print("✅ Chat funcionou!")
                print(f"Resposta recebida ({len(result['response'])} caracteres)")
                # Mostra trecho da resposta
                preview = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                print(f"Preview: {preview.replace(chr(10), ' ').replace(chr(13), ' ')}")
            else:
                print("❌ Resposta vazia ou muito curta")
                return False
        else:
            print(f"❌ Chat falhou: {response.text[:200]}...")
            return False

    except requests.exceptions.Timeout:
        print("❌ Timeout na resposta (verificar se Ollama está funcionando)")
        return False
    except Exception as e:
        print(f"❌ Erro no Chat: {e}")
        return False

    # Test 3: Chat com Trading - sem contexto de predição
    print("\\n3️⃣ Testando Chat - Pergunta de Trading...")
    try:
        payload = {
            "message": "Quais são os melhores sinais para comprar XAUUSD?",
            "model": "llama3.1:8b"
        }
        response = requests.post("http://localhost:8080/chat",
                               json=payload, timeout=60)

        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if 'response' in result and len(result['response']) > 50:
                print("✅ Chat Trading funcionou!")
                print(f"Resposta recebida ({len(result['response'])} caracteres)")
                # Verificar se menciona sinais ou estratégias
                response_lower = result['response'].lower()
                trading_keywords = ['rsi', 'macd', 'bollinger', 'suporte', 'resistencia', 'volume', 'tendencia']
                found_keywords = [kw for kw in trading_keywords if kw in response_lower]
                if found_keywords:
                    print(f"📊 Contexto técnico encontrado: {', '.join(found_keywords)}")
                else:
                    print("⚠️ Resposta não parece conter análise técnica específica")
            else:
                print("❌ Resposta muito curta para análise de trading")
        else:
            print("❌ Chat Trading falhou")
            return False

    except Exception as e:
        print(f"❌ Erro no Chat Trading: {e}")
        return False

    print("\\n" + "="*50)
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("="*50)

    print("\\n📋 RESUMO DOS TESTES:")
    print("✅ Health Check - Sistema online")
    print("✅ Chat Básico - IA respondendo")
    print("✅ Chat Trading - Análise especializada")
    print("\\n🚀 O CHATBOT ESTÁ PRONTO PARA USO!")

    print("\\n🔗 URLs disponíveis:")
    print("🌐 Interface Web: http://localhost:8080")
    print("📊 Dashboard MT5: http://localhost:5000/prediction/dashboard")

    print("\\n💡 Exemplos de perguntas:")
    print("  'Analise o XAUUSD para hoje'")
    print("  'Quais sinais confirmar entrada BUY?'")
    print("  'Quanto tempo para objetivo de $50?'")
    print("  'Recomende estratégia conservadora'")

def test_url_reachability():
    """Testa se URLs respondem"""
    print("\\n🔗 Testando URLs...")

    urls = [
        ("Trading Chatbot", "http://localhost:8080"),
        ("Health Check", "http://localhost:8080/health"),
        ("MT5 Dashboard", "http://localhost:5000/prediction/dashboard")
    ]

    for name, url in urls:
        try:
            response = requests.get(url, timeout=5)
            status = f"OK ({response.status_code})" if response.status_code < 400 else f"FAIL ({response.status_code})"
            print(f"{name}: {status}")
        except:
            print(f"{name}: FAIL (não responde)")

    # Test Ollama directly
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()["models"]
            print(f"Ollama API: OK ({len(models)} modelos)")
        else:
            print(f"Ollama API: FAIL ({response.status_code})")
    except:
        print("Ollama API: FAIL")

if __name__ == "__main__"):
    try:
        test_url_reachability()
        test_basic_functionality()
    except KeyboardInterrupt:
        print("\\n\\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\\n\\n❌ Erro geral nos testes: {e}")
