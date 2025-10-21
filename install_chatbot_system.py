#!/usr/bin/env python3
"""
Sistema de Instalação do Chatbot IA para Trading
Instala e configura: Ollama + OpenWebUI + Integração com Motor de Predição
"""

import subprocess
import sys
import os
import time
import requests
import json
from pathlib import Path

class TradingChatbotInstaller:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.ollama_url = "http://localhost:11434"
        self.openwebui_port = 8080
        self.openwebui_url = f"http://localhost:{self.openwebui_port}"

        # Configurações dos modelos
        self.models_to_install = [
            "mistral",  # Modelo mais rápida e eficiente
            "llama2:7b"  # Alternativa se mistral falhar
        ]

    def run_command(self, cmd, description="Executando comando", shell=False):
        """Executa comando do sistema com feedback"""
        print(f"[EXEC] {description}...")
        print(f"CMD: {cmd}")

        try:
            if shell:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run(cmd.split(), capture_output=True, text=True)

            if result.returncode == 0:
                print(f"[OK] {description}")
                if result.stdout:
                    print(f"Output: {result.stdout.strip()}")
                return True
            else:
                print(f"[FAIL] {description}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"[ERROR] {description}: {str(e)}")
            return False

    def check_python_dependencies(self):
        """Verifica e instala dependências Python necessárias"""
        required_packages = [
            "requests",
            "flask",
            "flask-cors"
        ]

        print("Checking Python dependencies...")

        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"[OK] {package}")
            except ImportError:
                print(f"Installing {package}...")
                if not self.run_command(f"pip install {package}", f"Installing {package}"):
                    print(f"[FAIL] Could not install {package}")
                    return False

        return True

    def install_ollama(self):
        """Instala o Ollama"""
        print("Installing Ollama...")

        # Para Windows, baixa o installer
        if sys.platform == "win32":
            print("Windows platform detected")

            # Tenta instalar via curl
            if self.run_command("where curl", "Checking curl", shell=True):
                print("Downloading Ollama via curl...")
                ollama_install = 'curl -fsSL https://ollama.com/install.bat | powershell'
                return self.run_command(ollama_install, "Installing Ollama", shell=True)
            else:
                print("[FAIL] Ollama needs manual installation from: https://ollama.com/download")
                print("Run this script again after installation")
                return False
        else:
            print("Linux/Mac platform - installing via official script")
            # Para Linux/Mac
            return self.run_command('curl -fsSL https://ollama.com/install.sh | sh',
                                   "Installing Ollama on Linux/Mac", shell=True)

    def start_ollama_service(self):
        """Inicia o serviço Ollama"""
        print("Starting Ollama service...")

        # Tenta iniciar Ollama
        if sys.platform == "win32":
            # No Windows, precisa executar ollama serve
            try:
                # Tenta executar em background usando subprocess
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)  # Aguarda inicialização
                print("[OK] Ollama started (background)")
                return True
            except:
                print("[FAIL] Could not start Ollama automatically")
                print("Run manually: ollama serve")
                return False
        else:
            # Linux/Mac pode usar systemctl ou iniciar diretamente
            return self.run_command("ollama serve", "Starting Ollama (will run in background)", shell=True)

    def pull_models(self):
        """Baixa modelos necessários"""
        print("Downloading AI models...")

        success = False
        for model in self.models_to_install:
            print(f"Downloading model: {model}")

            if self.run_command(f"ollama pull {model}", f"Downloading {model}"):
                success = True
                break  # Usa o primeiro modelo que conseguir baixar
            else:
                print(f"Warning: Failed to download {model}, trying next...")

        if not success:
            print("[FAIL] Could not download any models")
            print("Run manually: ollama pull mistral")
            return False

        return True

    def install_openwebui(self):
        """Instala o OpenWebUI"""
        print("Installing OpenWebUI...")

        try:
            # Instala via pip
            if self.run_command("pip install open-webui", "Installing OpenWebUI"):
                print("[OK] OpenWebUI installed via pip")

                # Cria script de inicialização
                startup_script = '''#!/bin/bash
# Script para iniciar OpenWebUI
echo "Iniciando OpenWebUI..."
open-webui serve --host 0.0.0.0 --port 8080
'''

                with open("start_openwebui.sh", "w") as f:
                    f.write(startup_script)

                # Também cria script Windows
                startup_bat = '''@echo off
echo Iniciando OpenWebUI...
open-webui serve --host 0.0.0.0 --port 8080
pause
'''

                with open("start_openwebui.bat", "w") as f:
                    f.write(startup_bat)

                print("📜 Scripts de inicialização criados:")
                print("🐧 Linux/Mac: ./start_openwebui.sh")
                print("🪟 Windows: start_openwebui.bat")

                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Erro ao instalar OpenWebUI: {e}")
            return False

    def test_ollama_connection(self):
        """Testa conexão com Ollama"""
        print("🔗 Testando conexão com Ollama...")

        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                print(f"✅ Ollama conectado - Modelos disponíveis: {len(models.get('models', []))}")

                for model in models.get('models', []):
                    print(f"  📦 {model.get('name', 'Unknown')}")
                return True
            else:
                print(f"❌ Ollama respondeu com código {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            print("❌ Não foi possível conectar ao Ollama")
            print("💡 Certifique-se que o Ollama está rodando: ollama serve")
            return False
        except Exception as e:
            print(f"❌ Erro ao testar Ollama: {e}")
            return False

    def create_trading_chatbot_api(self):
        """Cria API de integração com o chatbot IA"""
        print("🤖 Criando API de integração do chatbot com motor de predição...")

        # Código da API de integração
        chatbot_api_code = '''#!/usr/bin/env python3
"""
API de Integração: Chatbot IA com Motor de Predição de Trading
Permite ao OpenWebUI fazer perguntas sobre o motor de predição
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import logging
from datetime import datetime

# Import motor de predição
try:
    from prediction_engine import PredictionEngine
    from models import PredictionRequest
except ImportError as e:
    print(f"Erro ao importar motor de predição: {e}")
    PredictionEngine = None

# Configuração logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permite requisições do OpenWebUI

# URLs
OLLAMA_URL = "http://localhost:11434"
PREDICTION_API_URL = "http://localhost:5000"  # Motor de predição existente

class TradingChatbotAssistant:
    """Assistente de trading que conecta IA com dados de predição"""

    def __init__(self):
        self.prediction_engine = None
        if PredictionEngine:
            try:
                self.prediction_engine = PredictionEngine()
                logger.info("Motor de predição conectado")
            except Exception as e:
                logger.error(f"Erro ao conectar motor de predição: {e}")

    def query_ollama(self, prompt, model="mistral"):
        """Consulta modelo Ollama"""
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Erro na API Ollama: {response.status_code}"

        except Exception as e:
            return f"Erro ao consultar Ollama: {str(e)}"

    def get_prediction_analysis(self, symbol, target_profit=None, balance=1000):
        """Obtém análise de predição atual"""
        try:
            if not self.prediction_engine:
                return "Motor de predição não disponível"

            # Cria requisição
            request_data = PredictionRequest(
                symbol=symbol.upper(),
                target_profit=float(target_profit or 50.0),
                balance=float(balance)
            )

            # Gera predição
            result = self.prediction_engine.predict(request_data)

            return {
                "estimated_operations": result.estimated_operations,
                "estimated_duration": result.estimated_duration_description,
                "success_probability": round(result.success_probability * 100, 1),
                "risk_level": result.risk_level,
                "backtest_results": result.backtest_results.to_dict() if result.backtest_results else "Dados históricos não disponíveis"
            }

        except Exception as e:
            logger.error(f"Erro na análise de predição: {e}")
            return f"Erro ao obter dados de predição: {str(e)}"

    def process_trading_question(self, question, model="mistral"):
        """Processa pergunta sobre trading e gera resposta"""

        # Identifica tipo de pergunta
        question_lower = question.lower()

        # Reunião de contextos baseada na pergunta
        context_parts = []

        # Sempre incluir dados atuais se perguntar sobre mercado ou predições
        if any(keyword in question_lower for keyword in ["mercado", "preço", "análise", "predição", "entr", "rsi", "macd"]):
            # Extrair símbolos mencionados
            symbols_mentioned = []
            for symbol in ["xauusd", "btcusd", "eurusd", "gbpusd", "usdjpy"]:
                if symbol.lower() in question_lower:
                    symbols_mentioned.append(symbol.upper())

            if symbols_mentioned:
                context_parts.append(f"Dados atuais do mercado para: {', '.join(symbols_mentioned)}")
                for symbol in symbols_mentioned:
                    prediction_data = self.get_prediction_analysis(symbol)
                    if isinstance(prediction_data, dict):
                        context_parts.append(f"""
{symbol}:
- Operações estimadas: {prediction_data['estimated_operations']}
- Tempo estimado: {prediction_data['estimated_duration']}
- Probabilidade de sucesso: {prediction_data['success_probability']}%
- Nível de risco: {prediction_data['risk_level']}
                        """.strip())

        # Prompt inteligente para Ollama baseado no contexto
        system_prompt = """Você é um assistente especialista em trading que combina análise técnica e dados reais.

REGRAS IMPORTANTES:
- Seja preciso e conservador nas recomendações
- Sempre mencione que a análise é educacional
- Use dados fornecidos na pergunta
- Recomende sempre gerenciamento de risco
- Não promova trading irresponsável

RESPONDA EM PORTUGUÊS BRASILEIRO.
"""

        context_text = "CONTEXTO ATUAL:\\n" + "\\n".join(context_parts) if context_parts else "Sem dados específicos disponíveis no momento."

        full_prompt = f"{system_prompt}\\n\\n{context_text}\\n\\nPERGUNTA: {question}\\n\\nRESPOSTA:"

        # Consulta IA
        logger.info(f"Consultando IA sobre: {question[:50]}...")
        response = self.query_ollama(full_prompt, model)

        return response

# Instância global
trading_assistant = TradingChatbotAssistant()

@app.route("/health")
def health_check():
    """Health check da API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ollama": test_ollama_connection(),
            "prediction_engine": trading_assistant.prediction_engine is not None
        }
    })

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    """Endpoint principal para conversação com chatbot"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                "error": "Campo 'message' obrigatório",
                "example": {"message": "Qual a probabilidade para XAUUSD?", "model": "mistral"}
            }), 400

        question = data['message']
        model = data.get('model', 'mistral')

        logger.info(f"Nova pergunta: {question[:100]}...")

        # Processa pergunta
        response = trading_assistant.process_trading_question(question, model)

        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model_used": model
        })

    except Exception as e:
        logger.error(f"Erro no chat endpoint: {e}")
        return jsonify({
            "error": f"Erro interno: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

def test_ollama_connection():
    """Testa conexão com Ollama"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🤖 Iniciando Trading Chatbot Assistant API...")
    print("📡 Endpoints:")
    print("  GET  /health  - Health check")
    print("  POST /chat    - Conversar com assistente (body: {'message': '...', 'model': 'mistral'})")
    print("🚀 Servindo em http://localhost:5001")

    app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == "__main__":
    main()
'''

        # Salva arquivo API
        api_file = self.base_dir / "trading_chatbot_api.py"
        with open(api_file, "w", encoding="utf-8") as f:
            f.write(chatbot_api_code)

        print(f"📁 API criada: {api_file}")
        print("🔗 Endpoint do chatbot: http://localhost:5001")

        return True

    def test_integration(self):
        """Testa integrações após instalação"""
        print("🧪 Testando integrações...")

        # Testa API do chatbot
        try:
            response = requests.get("http://localhost:5001/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ API do chatbot funcionando")
                print(f"   Ollama: {'✅' if data['services']['ollama'] else '❌'}")
                print(f"   Motor de predição: {'✅' if data['services']['prediction_engine'] else '❌'}")

                # Testa chat
                test_question = "Qual a probabilidade de sucesso para XAUUSD?"
                chat_response = requests.post("http://localhost:5001/chat",
                    json={"message": test_question}, timeout=30)

                if chat_response.status_code == 200:
                    print("✅ Chatbot funcionando")
                    print(f"   Resposta de teste: {chat_response.json()['response'][:100]}...")
                else:
                    print("⚠️ Chatbot iniciou mas sem resposta")

                return True
            else:
                print("❌ API do chatbot não responde")
                return False

        except Exception as e:
            print(f"❌ Erro ao testar integrações: {e}")
            return False

    def create_startup_scripts(self):
        """Cria scripts de inicialização do sistema completo"""
        print("📜 Criando scripts de inicialização...")

        # Script principal para iniciar tudo
        main_startup = '''#!/bin/bash
# Script completo para iniciar: Ollama + OpenWebUI + Trading Chatbot API
echo "=========================================="
echo "🤖 SISTEMA TRADING CHATBOT - INICIALIZANDO"
echo "=========================================="

echo ""
echo "1️⃣ Iniciando Ollama..."
# Verifica se Ollama já está rodando
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama já está rodando"
else
    echo "🚀 Iniciando Ollama..."
    nohup ollama serve > ollama.log 2>&1 &
    sleep 3
fi

echo ""
echo "2️⃣ Iniciando Trading Chatbot API..."
# Verifica se API já está rodando
if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ Trading Chatbot API já está rodando"
else
    echo "🚀 Iniciando Trading Chatbot API..."
    nohup python trading_chatbot_api.py > chatbot.log 2>&1 &
    sleep 2
fi

echo ""
echo "3️⃣ Iniciando OpenWebUI..."
# Verifica se OpenWebUI já está rodando
if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ OpenWebUI já está rodando"
else
    echo "🚀 Iniciando OpenWebUI..."
    nohup open-webui serve --host 0.0.0.0 --port 8080 > openwebui.log 2>&1 &
    sleep 3
fi

echo ""
echo "4️⃣ Verificando status dos serviços..."
echo "🔗 Ollama: http://localhost:11434"
echo "🔗 Trading Chatbot API: http://localhost:5001"
echo "🔗 OpenWebUI: http://localhost:8080"
echo "🔗 Motor de Predição: http://localhost:5000"

echo ""
echo "🧪 Testando conexões..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama OK"
else
    echo "❌ Ollama FALHA"
fi

if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ Chatbot API OK"
else
    echo "❌ Chatbot API FALHA"
fi

if curl -s http://localhost:8080 > /dev/null; then
    echo "✅ OpenWebUI OK"
else
    echo "❌ OpenWebUI FALHA"
fi

echo ""
echo "🎉 SISTEMA PRONTO!"
echo "📱 Acesse o chatbot em: http://localhost:8080"
echo "📊 Dashboard de predição em: http://localhost:5000/prediction/dashboard"
echo ""
echo "💡 Digite: 'Me ajude com análise de trading no XAUUSD'"
echo "=========================================="
'''

        with open("start_trading_chatbot.sh", "w") as f:
            f.write(main_startup)

        # Versão Windows
        startup_bat = '''@echo off
echo ==========================================
echo 🤖 SISTEMA TRADING CHATBOT - INICIALIZANDO
echo ==========================================
echo.

echo 1️⃣ Verificando Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama já está rodando
) else (
    echo 🚀 Iniciando Ollama...
    start /B ollama serve > ollama.log 2>&1
    timeout /t 3 >nul
)

echo.
echo 2️⃣ Verificando Trading Chatbot API...
curl -s http://localhost:5001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Trading Chatbot API já está rodando
) else (
    echo 🚀 Iniciando Trading Chatbot API...
    start /B python trading_chatbot_api.py > chatbot.log 2>&1
    timeout /t 2 >nul
)

echo.
echo 3️⃣ Verificando OpenWebUI...
curl -s http://localhost:8080 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ OpenWebUI já está rodando
) else (
    echo 🚀 Iniciando OpenWebUI...
    start /B open-webui serve --host 0.0.0.0 --port 8080 > openwebui.log 2>&1
    timeout /t 3 >nul
)

echo.
echo 4️⃣ Status dos serviços:
echo 🔗 Ollama: http://localhost:11434
echo 🔗 Trading Chatbot API: http://localhost:5001
echo 🔗 OpenWebUI: http://localhost:8080
echo 🔗 Motor de Predição: http://localhost:5000

echo.
echo 🎉 SISTEMA PRONTO!
echo 📱 Acesse o chatbot em: http://localhost:8080
echo 📊 Dashboard de predição em: http://localhost:5000/prediction/dashboard
echo.
echo Pressione qualquer tecla para continuar...
pause >nul
'''

        with open("start_trading_chatbot.bat", "w") as f:
            f.write(startup_bat)

        print("📜 Scripts criados:")
        print("🐧 Linux/Mac: ./start_trading_chatbot.sh")
        print("🪟 Windows: start_trading_chatbot.bat")

        return True

    def main(self):
        """Execução principal da instalação"""
        print("TRADING CHATBOT IA INSTALLER")
        print("============================================")
        print("This script will install and configure:")
        print("* Ollama (AI engine)")
        print("* OpenWebUI (web interface)")
        print("* Trading Chatbot API (integration)")
        print()

        success_count = 0
        total_steps = 7

        # 1. Check Python
        print(f"Step 1/{total_steps}: Checking Python dependencies...")
        if self.check_python_dependencies():
            success_count += 1
        else:
            print("[FAIL] Critical failure - Python dependencies required")
            return False

        # 2. Install Ollama
        print(f"\nStep 2/{total_steps}: Installing Ollama...")
        if self.install_ollama():
            success_count += 1
        else:
            print("[WARN] Ollama may need manual installation")

        # 3. Start Ollama
        print(f"\nStep 3/{total_steps}: Starting Ollama service...")
        if self.start_ollama_service():
            # Test connection after a few seconds
            time.sleep(5)
            if self.test_ollama_connection():
                success_count += 1
            else:
                print("[WARN] Ollama started but no connection")
        else:
            print("[WARN] Ollama may need manual start")

        # 4. Download models
        print(f"\nStep 4/{total_steps}: Downloading AI models...")
        if self.pull_models():
            success_count += 1
        else:
            print("[WARN] Failed to download models")

        # 5. Install OpenWebUI
        print(f"\nStep 5/{total_steps}: Installing OpenWebUI...")
        if self.install_openwebui():
            success_count += 1
        else:
            print("[WARN] Failed to install OpenWebUI")

        # 6. Create API integration
        print(f"\nStep 6/{total_steps}: Creating integration API...")
        if self.create_trading_chatbot_api():
            success_count += 1
        else:
            print("[WARN] Failed to create API")

        # 7. Create startup scripts
        print(f"\nStep 7/{total_steps}: Creating startup scripts...")
        if self.create_startup_scripts():
            success_count += 1

        # 8. Test integrations (bonus step)
        print("\nTesting integrations...")
        if self.test_integration():
            print("[OK] System working!")
        else:
            print("[WARN] Some components may need adjustments")

        print("\n" + "="*50)
        print(f"INSTALLATION SUMMARY: {success_count}/{total_steps} components OK")
        print("="*50)

        if success_count >= 5:
            print("INSTALLATION MOSTLY SUCCESSFUL!")
            print("\\n📋 PRÓXIMOS PASSOS:")
            print("1. Execute: ./start_trading_chatbot.sh (Linux/Mac) ou start_trading_chatbot.bat (Windows)")
            print("2. Acesse http://localhost:8080 no navegador")
            print("3. Teste perguntando: 'Ajude-me com análise de trading no XAUUSD'")
            print("\\n🔗 URLs importantes:")
            print("📱 Chatbot IA: http://localhost:8080")
            print("📊 Dashboard: http://localhost:5000/prediction/dashboard")
            print("🤖 API do Chatbot: http://localhost:5001")
            print("⚙️ Ollama: http://localhost:11434")
        else:
            print("⚠️ PROBLEMAS DETECTADOS")
            print("Consulte os logs acima e reinstale componentes faltantes")

        print("\\n💡 Para suporte, verifique os arquivos de log gerados")
        print("="*50)

        return success_count >= 5

if __name__ == "__main__":
    installer = TradingChatbotInstaller()
    installer.main()
