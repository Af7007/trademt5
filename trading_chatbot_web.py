#!/usr/bin/env python3
"""
Interface Web do Chatbot de Trading IA
Substitui OpenWebUI com solução customizada
Integra Chatbot IA com Motor de Predição de Trading
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, render_template_string, Response
from flask_cors import CORS
import requests
import json
import logging
from datetime import datetime
import time

# Import motor de predição
try:
    from prediction_engine import PredictionEngine
    from models import PredictionRequest
except ImportError as e:
    print(f"Aviso: Motor de predicao nao disponivel: {e}")
    PredictionEngine = None

# URLs
OLLAMA_URL = "http://localhost:11434"
PREDICTION_API_URL = "http://localhost:5000"

app = Flask(__name__)
CORS(app)

# Configuração logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingChatbotWeb:
    """Interface web para chatbot de trading"""

    def __init__(self):
        self.prediction_engine = None
        if PredictionEngine:
            try:
                self.prediction_engine = PredictionEngine()
                logger.info("Motor de predicao conectado")
            except Exception as e:
                logger.error(f"Erro ao conectar motor de predicao: {e}")

        # Histórico de conversas
        self.conversation_history = []

    def query_ollama(self, prompt, model="llama3.1:8b"):
        """Consulta modelo Ollama"""
        try:
            start_time = time.time()

            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True  # Streaming para melhor UX
                },
                stream=True,
                timeout=60
            )

            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                full_response += data['response']
                                # Yield chunk for streaming
                                yield data['response']
                        except:
                            continue

                processing_time = time.time() - start_time
                logger.info(f"IA respondeu em {processing_time:.2f}s")
                return full_response
            else:
                return f"Erro na API Ollama: {response.status_code}"

        except Exception as e:
            return f"Erro ao consultar Ollama: {str(e)}"

    def get_prediction_analysis(self, symbol, target_profit=None, balance=1000):
        """Obtém análise de predição atual"""
        try:
            if not self.prediction_engine:
                return "Motor de predicao nao disponivel"

            request_data = PredictionRequest(
                symbol=symbol.upper(),
                target_profit=float(target_profit or 50.0),
                balance=float(balance)
            )

            result = self.prediction_engine.predict(request_data)

            return {
                "operacoes_estimadas": result.estimated_operations,
                "tempo_estimado": result.estimated_duration_description,
                "probabilidade_sucesso": round(result.success_probability * 100, 1),
                "nivel_risco": result.risk_level,
                "dados_historicos": result.backtest_results.to_dict() if result.backtest_results else "Dados históricos não disponíveis"
            }

        except Exception as e:
            logger.error(f"Erro na analise de predicao: {e}")
            return f"Erro ao obter dados de predicao: {str(e)}"

    def process_trading_question(self, question, model="llama3.1:8b"):
        """Processa pergunta sobre trading e gera resposta inteligente"""

        question_lower = question.lower()

        # Extrair símbolos mencionados e incluir dados de predição
        context_parts = []
        symbols_mentioned = []
        supported_symbols = ["xauusd", "btcusd", "eurusd", "gbpusd", "usdjpy"]

        for symbol in supported_symbols:
            if symbol.lower() in question_lower:
                symbols_mentioned.append(symbol.upper())

        if symbols_mentioned:
            context_parts.append(f"=== DADOS ATUAIS DO MERCADO ===")
            for symbol in symbols_mentioned:
                prediction_data = self.get_prediction_analysis(symbol)
                if isinstance(prediction_data, dict):
                    context_parts.append(f"""
{symbol}:
- Operacoes estimadas: {prediction_data['operacoes_estimadas']}
- Tempo estimado: {prediction_data['tempo_estimado']}
- Probabilidade de sucesso: {prediction_data['probabilidade_sucesso']}%
- Nivel de risco: {prediction_data['nivel_risco']}
                    """.strip())

        # Prompt otimizado para velocidade e clareza
        system_instructions = """ATENÇÃO: Você é especialista em trading. Sempre mencione que análises são EDUCACIONAIS e não garantem lucro. Use dados fornecidos. Recomende sempre gestão de risco.

RESPONDA EM PORTUGUÊS BRASILEIRO - SEJA CONCISO mas completo. Foque em:
- Probabilidades (não certezas)
- Estratégias conservadoras
- Gestão de risco obrigatória

Formate de forma clara e organizada.
"""

        # Construir contexto completo
        if context_parts:
            context_text = "\\n".join(context_parts)
        else:
            context_text = "Sem dados especificos do mercado no momento."

        full_prompt = f"{system_instructions}\\n\\n{context_text}\\n\\n=== PERGUNTA DO USUARIO ===\\n{question}\\n\\n=== SUA RESPOSTA ===\\n"

        logger.info(f"Processando pergunta sobre trading: {question[:50]}...")

        # Consulta IA com limite de tamanho de prompt
        # Truncar prompt se for muito longo para performance
        max_prompt_size = 4000  # limite para performance
        if len(full_prompt) > max_prompt_size:
            # Manter o sistema prompt + contexto essencial + pergunta
            truncated_prompt = full_prompt[:max_prompt_size]
            logger.warning(f"Prompt truncado de {len(full_prompt)} para {max_prompt_size} caracteres")
        else:
            truncated_prompt = full_prompt

        # Consulta IA
        response = ""
        for chunk in self.query_ollama(truncated_prompt, model):
            response += chunk
            yield chunk

        # Salvar no histórico
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": response,
            "model": model,
            "symbols_analyzed": symbols_mentioned
        })

        # Manter apenas últimas 50 conversas
        self.conversation_history = self.conversation_history[-50:]

# Instância global
chatbot = TradingChatbotWeb()

# Interface web HTML
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading AI Assistant - Chatbot Especializado</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .chat-container {
            height: calc(100vh - 200px);
            overflow-y: auto;
        }
        .message-user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .message-assistant {
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        }
        .typing-indicator {
            display: none;
        }
        .typing-indicator.show {
            display: flex;
        }
        @keyframes typing {
            0%, 60%, 100% { opacity: 0; }
            30% { opacity: 1; }
        }
        .typing-dot {
            animation: typing 1.4s infinite ease-in-out;
        }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    </style>
</head>
<body class="bg-gray-100">
    <!-- Header -->
    <header class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold flex items-center">
                        <i class="fas fa-robot mr-3"></i>
                        Trading AI Assistant
                    </h1>
                    <p class="text-sm opacity-90">Especialista em Forex & Commodities</p>
                </div>
                <div class="text-right">
                    <div id="status-indicator" class="flex items-center justify-end">
                        <span class="h-3 w-3 bg-green-400 rounded-full mr-2"></span>
                        <span class="text-sm">Sistema Online</span>
                    </div>
                    <div class="text-xs opacity-75 mt-1" id="current-time"></div>
                </div>
            </div>
        </div>
    </header>

    <div class="container mx-auto px-4 py-6 max-w-4xl">
        <!-- Info Panel -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                <div class="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                    <i class="fas fa-brain text-3xl text-green-600 mb-2"></i>
                    <div class="text-lg font-bold text-green-700">IA Especializada</div>
                    <div class="text-sm text-gray-600">Llama 3.1 & DeepSeek</div>
                </div>
                <div class="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                    <i class="fas fa-chart-line text-3xl text-blue-600 mb-2"></i>
                    <div class="text-lg font-bold text-blue-700">Dados Reais</div>
                    <div class="text-sm text-gray-600">XAUUSD, BTCUSD, EURUSD</div>
                </div>
                <div class="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                    <i class="fas fa-shield text-3xl text-purple-600 mb-2"></i>
                    <div class="text-lg font-bold text-purple-700">Risk Management</div>
                    <div class="text-sm text-gray-600">Análise Conservadora</div>
                </div>
            </div>
        </div>

        <!-- Chat Container -->
        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
            <!-- Chat Messages -->
            <div id="chat-container" class="chat-container p-6 space-y-4"></div>

            <!-- Typing Indicator -->
            <div class="typing-indicator px-6 pb-4" id="typing-indicator">
                <div class="flex items-center space-x-2">
                    <i class="fas fa-robot text-purple-600"></i>
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-purple-600 rounded-full typing-dot"></div>
                        <div class="w-2 h-2 bg-purple-600 rounded-full typing-dot"></div>
                        <div class="w-2 h-2 bg-purple-600 rounded-full typing-dot"></div>
                    </div>
                    <span class="text-sm text-gray-600">Analisando mercado...</span>
                </div>
            </div>

            <!-- Input Form -->
            <div class="border-t bg-gray-50 p-4">
                <div class="flex space-x-4">
                    <div class="flex-1">
                        <input type="text" id="message-input"
                               placeholder="Ex: 'Ajude-me com análise de trading no XAUUSD hoje'"
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent">
                    </div>
                    <select id="model-select" class="px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500">
                        <option value="llama3.1:8b">Llama 3.1 (Fast)</option>
                        <option value="deepseek-r1:latest">DeepSeek (Smart)</option>
                    </select>
                    <button id="send-button" class="gradient-bg text-white px-6 py-3 rounded-lg hover:opacity-90 transition duration-200 flex items-center">
                        <i class="fas fa-paper-plane mr-2"></i>
                        Enviar
                    </button>
                </div>

                <!-- Quick Questions -->
                <div class="mt-3 flex flex-wrap gap-2">
                    <button class="quick-question bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded-full text-sm" data-question="Analise o XAUUSD para hoje">
                        XAUUSD Hoje
                    </button>
                    <button class="quick-question bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded-full text-sm" data-question="Quais sinais para entrada BUY no EURUSD?">
                        Sinais BUY
                    </button>
                    <button class="quick-question bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded-full text-sm" data-question="Quanto tempo para objetivo de $50?">
                        Tempo Meta
                    </button>
                    <button class="quick-question bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded-full text-sm" data-question="Avalie o risco da estrategia atual">
                        Avaliar Risco
                    </button>
                    <button class="quick-question bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded-full text-sm" data-question="Recomende melhores horarios para operar">
                        Melhores Horários
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Atualizar hora
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = now.toLocaleString('pt-BR');
        }
        setInterval(updateTime, 1000);
        updateTime();

        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const modelSelect = document.getElementById('model-select');
        const typingIndicator = document.getElementById('typing-indicator');

        // Quick questions
        document.querySelectorAll('.quick-question').forEach(button => {
            button.addEventListener('click', function() {
                messageInput.value = this.dataset.question;
                sendMessage();
            });
        });

        // Send message on Enter
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Send button click
        sendButton.addEventListener('click', sendMessage);

        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Add user message to chat
            addMessage('user', message);
            messageInput.value = '';

            // Show typing indicator
            typingIndicator.classList.add('show');

            // Send to API
            const selectedModel = modelSelect.value;
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    model: selectedModel
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                typingIndicator.classList.remove('show');

                if (data.error) {
                    addMessage('assistant', 'Erro: ' + data.error);
                } else {
                    // For streaming responses, we'll receive the full response at once
                    addMessage('assistant', data.response || 'Resposta vazia recebida');
                }
            })
            .catch(error => {
                typingIndicator.classList.remove('show');
                console.error('Error:', error);
                addMessage('assistant', 'Erro de conexao com o servidor: ' + error.message);
            });

            // Add placeholder for assistant response (will be replaced with streaming)
            // For now, we'll use non-streaming as it's simpler for the implementation
        }

        function addMessage(sender, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message message-${sender} p-4 rounded-lg`;

            if (sender === 'user') {
                messageDiv.innerHTML = `
                    <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-white rounded-full flex items-center justify-center">
                                <i class="fas fa-user text-purple-600"></i>
                            </div>
                        </div>
                        <div class="flex-1">
                            <div class="font-semibold text-purple-700 mb-1">Você</div>
                            <div class="text-white">${escapeHtml(content)}</div>
                        </div>
                    </div>
                `;
            } else {
                messageDiv.innerHTML = `
                    <div class="flex items-start space-x-3">
                        <div class="flex-shrink-0">
                            <div class="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                                <i class="fas fa-robot text-white"></i>
                            </div>
                        </div>
                        <div class="flex-1">
                            <div class="font-semibold text-gray-700 mb-1">Trading AI Assistant</div>
                            <div class="text-gray-800 prose prose-sm max-w-none">${formatResponse(content)}</div>
                        </div>
                    </div>
                `;
            }

            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function escapeHtml(text) {
            const map = {
                '&': '&',
                '<': '<',
                '>': '>',
                '"': '"',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, function(m) { return map[m]; });
        }

        function formatResponse(text) {
            // Simple formatting for trading responses
            return text
                .replace(/^### (.*$)/gim, '<h3 class="font-bold text-lg mt-4 mb-2">$1</h3>')
                .replace(/^## (.*$)/gim, '<h3 class="font-bold mt-3 mb-2">$1</h3>')
                .replace(/^# (.*$)/gim, '<h2 class="font-bold text-xl mt-4 mb-2">$1</h2>')
                .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
                .replace(/\*(.*)\*/gim, '<em>$1</em>')
                .replace(/^- (.*$)/gim, '<li class="ml-4">$1</li>')
                .replace(/`([^`]+)`/gim, '<code class="bg-gray-200 px-1 rounded">$1</code>')
                .split('\\n').join('<br>');
        }

        // Initial welcome message
        setTimeout(() => {
            addMessage('assistant', `
                <strong>Olá! Sou seu Trading AI Assistant 🎯</strong><br><br>

                Posso ajudá-lo com análise técnica especializada em Forex e Commodities.
                Tenho acesso a dados reais de mercado e posso responder perguntas sobre:<br><br>

                • <strong>Análise de Símbolos:</strong> XAUUSD, BTCUSD, EURUSD, GBPUSD, USDJPY<br>
                • <strong>Probabilidades e Riscos</strong> baseados em dados atuais<br>
                • <strong>Estratégias de Entrada/Saída</strong> com sinais específicos<br>
                • <strong>Melhores Horários</strong> para operar<br>
                • <strong>Gerenciamento de Risco</strong> profissional<br><br>

                <em>Lembre-se: Esta é uma ferramenta educacional. Sempre gerencie riscos adequadamente!</em>
            `);
        }, 1000);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    """Página principal do chatbot"""
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    """Endpoint de chat sem streaming (mais simples e compatível)"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({
                "error": "Campo 'message' obrigatório",
                "example": {"message": "Sua pergunta aqui"}
            }), 400

        question = data['message']
        model = data.get('model', 'llama3.1:8b')

        logger.info(f"Pergunta recebida: {question[:100]}...")

        # Processar pergunta com timeout e melhor tratemento
        try:
            logger.info("Iniciando processamento da pergunta...")

            # Processar pergunta (converter generator para string completa)
            response_text = ""
            chunk_count = 0

            start_process = time.time()
            timeout_limit = 45  # segundos

            for chunk in chatbot.process_trading_question(question, model):
                response_text += chunk
                chunk_count += 1

                # Timeout para evitar travamentos
                if time.time() - start_process > timeout_limit:
                    logger.warning(f"Timeout excedido após {timeout_limit}s - finalizando resposta parcial")
                    break

                # Log progressivo para debugging
                if chunk_count % 50 == 0:
                    logger.info(f"Processado {chunk_count} chunks, tamanho atual: {len(response_text)}")

            processing_time = time.time() - start_process
            logger.info(f"Processamento completo em {processing_time:.2f}s")

            # Verificar se resposta foi gerada
            if len(response_text.strip()) == 0:
                logger.error("Resposta vazia gerada pela IA")
                return jsonify({
                    "error": "IA não conseguiu gerar resposta. Verifique se o Ollama está funcionando.",
                    "model": model
                }), 500

            # Se resposta muito curta, pode ser problema da IA
            if len(response_text.strip()) < 10:
                logger.warning(f"Resposta muito curta: '{response_text}' - possivel problema na IA")

            logger.info(f"Resposta gerada com sucesso: {len(response_text)} caracteres")

            return jsonify({
                "response": response_text,
                "model": model,
                "question": question,
                "timestamp": datetime.now().isoformat()
            })

        except requests.exceptions.Timeout:
            logger.error("Timeout na resposta da IA")
            return jsonify({
                "error": "Timeout: IA demorou muito para responder",
                "suggestion": "Tente novamente ou use um modelo mais rápido"
            }), 504

        except Exception as process_error:
            logger.error(f"Erro no processamento: {process_error}")
            return jsonify({
                "error": f"Erro interno: {str(process_error)}",
                "suggestion": "Verifique logs do servidor para mais detalhes"
            }), 500

    except Exception as e:
        logger.error(f"Erro geral no chat: {e}")
        return jsonify({
            "error": f"Erro interno: {str(e)}"
        }), 500

@app.route("/health")
def health():
    """Status do sistema"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "models": {
            "ollama_available": test_ollama_connection(),
            "prediction_engine": chatbot.prediction_engine is not None
        },
        "conversation_count": len(chatbot.conversation_history)
    })

def test_ollama_connection():
    """Testa conexão com Ollama"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("Trading AI Assistant - Starting server...")
    print("URLs:")
    print("  Chatbot Web: http://localhost:8080")
    print("  MT5 Dashboard: http://localhost:5000/prediction/dashboard")
    print("  Health Check: http://localhost:8080/health")
    print("  Chat API: POST http://localhost:8080/chat")
    print("")
    print("Example questions:")
    print("  'Analyze XAUUSD for today'")
    print("  'What signals for BUY entry?'")
    print("  'How long for $50 goal?'")
    print("  'Evaluate current strategy risk'")
    print("")
    print("Server running...")

    app.run(host='0.0.0.0', port=8080, debug=False)

if __name__ == "__main__":
    main()
