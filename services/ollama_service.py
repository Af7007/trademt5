"""
Ollama Integration Service
Gerencia comunicação com modelos de linguagem locais via Ollama API
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
import threading
import logging

logger = logging.getLogger(__name__)


class OllamaService:
    """Serviço para interação com modelos Ollama"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral"):
        self.base_url = base_url
        self.default_model = model
        self.timeout = 60  # segundos
        self.session = requests.Session()

        # Cache para modelos disponíveis
        self._available_models = None
        self._last_model_check = 0

    def _format_error(self, error_msg: str, details: Any = None) -> Dict[str, Any]:
        """Formata resposta de erro"""
        return {
            "success": False,
            "error": error_msg,
            "details": details,
            "timestamp": time.time()
        }

    def _format_success(self, data: Any, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Formata resposta de sucesso"""
        response = {
            "success": True,
            "data": data,
            "timestamp": time.time()
        }
        if metadata:
            response.update(metadata)
        return response

    def check_connection(self) -> Dict[str, Any]:
        """Verifica se Ollama está rodando e acessível"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return self._format_success({
                    "ollama_running": True,
                    "status": "connected"
                })
            else:
                return self._format_error("Ollama respondeu com status diferente de 200",
                                        {"status_code": response.status_code})
        except requests.RequestException as e:
            return self._format_error("Não foi possível conectar ao Ollama",
                                    {"error": str(e), "endpoint": self.base_url})

    def list_models(self, refresh: bool = False) -> Dict[str, Any]:
        """Lista modelos disponíveis no Ollama"""
        try:
            # Cache por 5 minutos
            current_time = time.time()
            if not refresh and self._available_models and (current_time - self._last_model_check) < 300:
                return self._format_success(self._available_models)

            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)

            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [model["name"] for model in models] if models else []

                result = {
                    "models": model_names,
                    "count": len(model_names),
                    "raw_data": models
                }

                # Cache
                self._available_models = result
                self._last_model_check = current_time

                return self._format_success(result)
            else:
                return self._format_error("Falha ao listar modelos",
                                        {"status_code": response.status_code})

        except requests.RequestException as e:
            return self._format_error("Erro de conexão ao listar modelos", {"error": str(e)})

    def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Baixa um modelo do Ollama"""
        try:
            data = {"name": model_name}
            response = self.session.post(f"{self.base_url}/api/pull",
                                       json=data,
                                       timeout=300)  # 5 minutos para download

            if response.status_code == 200:
                return self._format_success({
                    "model": model_name,
                    "status": "downloaded",
                    "message": "Modelo baixado com sucesso"
                })
            else:
                return self._format_error("Falha ao baixar modelo",
                                        {"model": model_name, "status_code": response.status_code})

        except requests.RequestException as e:
            return self._format_error("Erro ao baixar modelo", {"model": model_name, "error": str(e)})

    def generate_text(self,
                      prompt: str,
                      model: Optional[str] = None,
                      stream: bool = False,
                      options: Optional[Dict] = None) -> Dict[str, Any]:
        """Gera texto usando um modelo Ollama"""
        try:
            model_to_use = model or self.default_model

            data = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": stream
            }

            if options:
                data["options"] = options

            response = self.session.post(f"{self.base_url}/api/generate",
                                       json=data,
                                       timeout=self.timeout)

            if response.status_code == 200:
                result = response.json()

                if stream:
                    # Para streaming, retornamos a resposta diretamente
                    return self._format_success(result)
                else:
                    # Para resposta direta, extraímos o texto
                    return self._format_success({
                        "text": result.get("response", ""),
                        "model": result.get("model", model_to_use),
                        "done": result.get("done", False),
                        "total_duration": result.get("total_duration"),
                        "load_duration": result.get("load_duration"),
                        "prompt_eval_count": result.get("prompt_eval_count"),
                        "eval_count": result.get("eval_count"),
                        "eval_duration": result.get("eval_duration")
                    })
            else:
                return self._format_error("Falha na geração de texto",
                                        {"status_code": response.status_code, "model": model_to_use})

        except requests.RequestException as e:
            model_used = model or self.default_model
            return self._format_error("Erro de conexão na geração", {"model": model_used, "error": str(e)})

    def chat_completion(self,
                       messages: List[Dict[str, str]],
                       model: Optional[str] = None,
                       options: Optional[Dict] = None) -> Dict[str, Any]:
        """Realiza uma conversa com formato de chat usando Ollama"""
        try:
            model_to_use = model or self.default_model

            # Converte mensagens para formato Ollama
            # Ollama usa um formato diferente - precisamos adaptar
            if len(messages) == 1:
                # Simplifica para geração de texto se for apenas uma mensagem
                prompt = messages[0].get("content", "")
                return self.generate_text(prompt, model_to_use, options=options)
            else:
                # Para conversas múltiplas, precisamos adaptar o formato
                conversation = ""
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "system":
                        conversation += f"System: {content}\n\n"
                    elif role == "user":
                        conversation += f"User: {content}\n\n"
                    elif role == "assistant":
                        conversation += f"Assistant: {content}\n\n"

                conversation += "Assistant: "

                return self.generate_text(conversation, model_to_use, options=options)

        except Exception as e:
            return self._format_error("Erro na conversação", {"error": str(e), "model": model or self.default_model})

    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Obtém informações sobre um modelo"""
        try:
            model = model_name or self.default_model
            response = self.session.post(f"{self.base_url}/api/show",
                                       json={"name": model},
                                       timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._format_success({
                    "model": model,
                    "license": data.get("license", ""),
                    "modelfile": data.get("modelfile", ""),
                    "parameters": data.get("parameters", ""),
                    "template": data.get("template", ""),
                    "details": data.get("details", {})
                })
            else:
                return self._format_error("Falha ao obter informações do modelo",
                                        {"model": model, "status_code": response.status_code})

        except requests.RequestException as e:
            return self._format_error("Erro de conexão ao obter info do modelo",
                                    {"model": model_name or self.default_model, "error": str(e)})

    # =============================== MÉTODOS ESPECÍFICOS PARA TRADING ================================

    def analyze_market_sentiment(self,
                                market_data: Dict,
                                asset: str = "BTCUSD") -> Dict[str, Any]:
        """Análise de sentimento de mercado usando IA"""
        try:
            # Prepara contexto de mercado
            context = f"""
Análise mercado atual para {asset}:

Dados de preço atuais:
- Bid: {market_data.get('bid', 'N/A')}
- Ask: {market_data.get('ask', 'N/A')}
- Spread: {market_data.get('spread', 'N/A')}

Indicadores técnicos:
- RSI: {market_data.get('rsi', 'N/A')}
- SMA20: {market_data.get('sma_20', 'N/A')}
- SMA50: {market_data.get('sma_50', 'N/A')}
- Bollinger Superior: {market_data.get('bb_upper', 'N/A')}
- Bollinger Inferior: {market_data.get('bb_lower', 'N/A')}

Posições abertas: {market_data.get('positions_count', 0)}
Último sinal: {market_data.get('last_signal', 'HOLD')}

Por favor, faça uma análise completa do mercado e forneça:
1. Sentiment atual (BULLISH/BEARISH/NEUTRAL)
2. Confiança na análise (0-100%)
3. Recomendação de ação (BUY/SELL/HOLD)
4. Razões da decisão
5. Próximos níveis importantes
"""

            response = self.generate_text(
                prompt=context,
                model="mistral",
                options={
                    "temperature": 0.3,  # Menos criativo, mais factual
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            )

            if response["success"]:
                return self._format_success({
                    "asset": asset,
                    "analysis": response["data"]["text"],
                    "model_used": "mistral",
                    "confidence_level": "medium",
                    "timestamp": time.time()
                })
            else:
                return response

        except Exception as e:
            return self._format_error("Erro na análise de sentimento", {"error": str(e), "asset": asset})

    def generate_trading_signals(self,
                               market_context: Dict,
                               risk_tolerance: str = "conservative") -> Dict[str, Any]:
        """Gera sinais de trading baseados no contexto de mercado"""
        try:
            risk_profile = {
                "conservative": "Foco em preservação de capital, high confidence signals only",
                "moderate": "Balance between risk and reward",
                "aggressive": "Accept higher volatility for better returns"
            }

            context = f"""
Gere sinais de trading profissional baseados nos dados de mercado:

Perfil de risco: {risk_tolerance}
{market_context.get('description', 'Dados de mercado disponíveis')}

Dados financeiros:
- Saldo da conta: {market_context.get('balance', 0)}
- Posições abertas: {market_context.get('positions', 0)}
- Margem disponível: {market_context.get('margin_free', 0)}

Últimas análises:
{market_context.get('recent_analysis', 'Nenhuma análise recente')}

Proporcione recomendações específicas incluindo:
1. Direção principal recomendada (BUY/SELL/HOLD)
2. Stop Loss recomendado
3. Take Profit recomendado
4. Tamanho da posição
5. Razão da recomendação
6. Fatores de risco
"""

            response = self.generate_text(
                prompt=context,
                model="mistral",
                options={
                    "temperature": 0.2,  # Muito conservador
                    "top_p": 0.8,
                    "max_tokens": 800
                }
            )

            if response["success"]:
                return self._format_success({
                    "signal": response["data"]["text"],
                    "risk_profile": risk_tolerance,
                    "model_used": "mistral",
                    "risk_level": risk_tolerance,
                    "timestamp": time.time()
                })
            else:
                return response

        except Exception as e:
            return self._format_error("Erro ao gerar sinais de trading", {"error": str(e)})

    def interpret_trading_results(self,
                                trades_history: List[Dict],
                                performance_metrics: Dict) -> Dict[str, Any]:
        """Interpreta resultados de trading e fornece insights"""
        try:
            history_summary = "\n".join([
                f"- Trade {trade.get('ticket', 'N/A')}: {trade.get('profit', 0):.2f} ({trade.get('symbol', 'N/A')})"
                for trade in trades_history[-10:]  # Últimos 10 trades
            ])

            context = f"""
Análise de performance de trading - Insights e Melhoria

Histórico recente de trades:
{history_summary}

Métricas de performance:
- Win Rate: {performance_metrics.get('win_rate', 0):.1f}%
- Total Profit: ${performance_metrics.get('total_profit', 0):.2f}
- Total Trades: {performance_metrics.get('total_trades', 0)}
- Winning Trades: {performance_metrics.get('winning_trades', 0)}
- Losing Trades: {performance_metrics.get('losing_trades', 0)}
- Average Win: ${performance_metrics.get('avg_profit', 0):.2f}
- Average Loss: ${performance_metrics.get('avg_loss', 0):.2f}

Por favor forneça:
1. Análise geral da performance
2. Pontos fortes e fracos
3. Recomendações de melhoria
4. Estratégias para próximo período
5. Análise de risco
"""

            response = self.generate_text(
                prompt=context,
                model="mistral",
                options={
                    "temperature": 0.4,
                    "top_p": 0.95,
                    "max_tokens": 600
                }
            )

            if response["success"]:
                return self._format_success({
                    "analysis": response["data"]["text"],
                    "model_used": "mistral",
                    "analysis_type": "performance_review",
                    "trades_analyzed": len(trades_history),
                    "timestamp": time.time()
                })
            else:
                return response

        except Exception as e:
            return self._format_error("Erro na análise de resultados", {"error": str(e)})


# Instância global do serviço Ollama
ollama_service = OllamaService()
