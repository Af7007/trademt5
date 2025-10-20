"""
API Documentation Routes
Rota para documentação da API Flask MLP Trading
"""

from flask import Blueprint, render_template_string

apidocs_bp = Blueprint('apidocs', __name__)

API_DOCUMENTATION_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - MLP Trading System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .endpoint { margin-bottom: 20px; border-left: 4px solid #007bff; padding-left: 15px; }
        .method { font-weight: bold; padding: 2px 6px; border-radius: 3px; }
        .method-get { background-color: #28a745; color: white; }
        .method-post { background-color: #dc3545; color: white; }
        .highlight { background-color: #fff3cd !important; }
        code { background-color: #f1f3f4; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">
                🤖 MLP Trading System - API Documentation
            </a>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="alert alert-info">
            <h4>📋 Notas Importantes:</h4>
            <ul>
                <li><strong>API Principal (Flask):</strong> <code>http://localhost:5000</code> - Sistema completo de trading</li>
                <li><strong>MCP Server:</strong> <code>http://localhost:3000</code> - Interface LLM com ferramentas</li>
                <li><strong>Django Dashboard:</strong> <code>http://localhost:5001</code> - Interface administrativa</li>
                <li><strong>Documentação API:</strong> <code>http://localhost:5000/apidocs</code> - Esta página</li>
            </ul>
        </div>

        <div class="jumbotron bg-light p-4">
            <h1 class="display-5">📊 API Reference</h1>
            <p class="lead">Documentação completa das APIs do sistema MLP Trading System</p>
        </div>

        <!-- BTC/USD Stats API -->
        <div class="card mt-4">
            <div class="card-header bg-info text-white">
                <h5>📈 BTC/USD Market Data</h5>
            </div>
            <div class="card-body">
                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/btcusd/stats</code>
                    <p>Dados completos de mercado BTC/USD: preços, estatísticas, posições, volatilidade</p>
                    <p class="text-muted">Response: Dados completos do MT5 em tempo real</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/btcusd/indicators/M1</code>
                    <p>Indicadores técnicos para timeframe M1</p>
                    <p class="text-muted">Response: RSI, MACD, Bollinger Bands, etc.</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/btcusd/analysis/M1</code>
                    <p>Análise técnica completa para timeframe M1</p>
                    <p class="text-muted">Response: Análise de tendência e força</p>
                </div>
            </div>
        </div>

        <!-- MLP Bot API -->
        <div class="card mt-4">
            <div class="card-header bg-success text-white">
                <h5>🤖 MLP Bot Control</h5>
            </div>
            <div class="card-body">
                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/mlp/health</code>
                    <p>Health check do sistema MLP</p>
                    <p class="text-muted">Response: Status de conectividade MT5/MLP</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/mlp/start</code>
                    <p>Iniciar bot MLP automático</p>
                    <p class="text-muted">Body: {} | Response: Status de início</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/mlp/stop</code>
                    <p>Parar bot MLP automático</p>
                    <p class="text-muted">Body: {} | Response: Status de parada</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/mlp/status</code>
                    <p>Status atual do bot MLP</p>
                    <p class="text-muted">Response: Status de execução, threshold, etc.</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/mlp/execute</code>
                    <p>Executar sinal manualmente</p>
                    <p class="text-muted">Body: { symbol, signal } | Response: Resultado da execução</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/mlp/analyze</code>
                    <p>Solicitar análise do mercado</p>
                    <p class="text-muted">Body: { symbol } | Response: Análise técnica</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/mlp/performance</code>
                    <p>Métricas de performance do sistema</p>
                    <p class="text-muted">Response: Win rate, P&L, drawdown, etc.</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/mlp/positions</code>
                    <p>Posições ativas abertas no MT5</p>
                    <p class="text-muted">Response: Lista de posições abertas</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/mlp/history</code>
                    <p>Histórico de análises MLP</p>
                    <p class="text-muted">Response: Lista de análises realizadas</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/mlp/trades</code>
                    <p>Histórico completo de trades(format)</p>
                    <p class="text-muted">Response: Todas operações realizadas</p>
                </div>
            </div>
        </div>

        <!-- API Bot Standalone (Integrated) -->
        <div class="card mt-4 highlight">
            <div class="card-header bg-danger text-white">
                <h5>🚀 BOT API STANDALONE (Porta: 5000)</h5>
                <small class="text-warning">API integrada do Bot Trading - Mesma porta do sistema principal</small>
            </div>
            <div class="card-body">
                <div class="alert alert-success">
                    <strong>✅ API Integrada:</strong> As rotas /bot estão integradas na porta 5000 junto com a API principal.
                    <br><strong>Opcionalmente executar separado:</strong> <code>python -m bot.api_controller</code> (porta 5001)
                    <br><strong>Base URL (integrada):</strong> <code>http://localhost:5000/bot/*</code>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/health</code>
                    <p>Health check da API Bot</p>
                    <p class="text-muted">Response: Status do sistema e MT5</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/start</code>
                    <p>Iniciar bot de trading</p>
                    <p class="text-muted">Body: {} | Response: Confirmação de início</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/stop</code>
                    <p>Parar bot de trading</p>
                    <p class="text-muted">Body: {} | Response: Confirmação de parada</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/bot/mlp-status</code>
                    <p>Status detalhado do bot MLP</p>
                    <p class="text-muted">Response: Status completo do sistema</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/bot/execute</code>
                    <p>Executar sinal BUY/SELL/HOLD</p>
                    <p class="text-muted">Body: { "signal": "BUY", "confidence": 0.85 } | Response: Resultado de execução</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/bot/analyze</code>
                    <p>Analisar mercado e executar automaticamente</p>
                    <p class="text-muted">Body: {} | Response: Análise de mercado com ação recomendada</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/bot/train</code>
                    <p>Treinar modelo MLP com dados históricos</p>
                    <p class="text-muted">Body: { "days": 30 } | Response: Status do treinamento</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/bot/emergency-close</code>
                    <p>Fechar todas as posições em emergência</p>
                    <p class="text-muted">Body: {} | Response: Status do fechamento forçado</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/bot/performance</code>
                    <p>Relatório de performance detalhado</p>
                    <p class="text-muted">Response: Métricas win rate, P&L, drawdown</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/bot/positions</code>
                    <p>Posições ativas atuais</p>
                    <p class="text-muted">Response: Lista de posições abertas no MT5</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/bot/market-data</code>
                    <p>Dados de mercado em tempo real</p>
                    <p class="text-muted">Query params: symbol=XAUUSD, timeframe=M5, count=100 | Response: Dados MT5</p>
                </div>

                <div class="mt-3 p-3 bg-light rounded">
                    <h6>📝 Como Usar Esta API:</h6>
                    <pre><code># ✅ 1. Já integrada na API principal (porta 5000)
# Rotas /bot/* disponíveis automaticamente

# 2. Testar endpoints
curl -X GET http://localhost:5000/bot/health
curl -X POST http://localhost:5000/bot/start -H "Content-Type: application/json" -d "{}"
curl -X POST http://localhost:5000/bot/execute -H "Content-Type: application/json" -d '{"signal": "BUY", "confidence": 0.85}'

# 🔄 3. Para executar separado (opcional)
python -m bot.api_controller  # Usará porta 5001</code></pre>
                </div>
            </div>
        </div>

        <!-- Scalping Bot API -->
        <div class="card mt-4">
            <div class="card-header bg-warning text-dark">
                <h5>🏃 Scalping Bot Control</h5>
            </div>
            <div class="card-body">
                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/scalping/dashboard</code>
                    <p>Dashboard principal do scalping bot</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/scalping/start</code>
                    <p>Iniciar bot de scalping</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/scalping/stop</code>
                    <p>Parar bot de scalping</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/scalping/status</code>
                    <p>Status do bot de scalping</p>
                </div>

                <div class="endpoint">
                    <span class="method method-post">POST</span>
                    <code>/scalping/execute-once</code>
                    <p>Executar uma operação única</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/scalping/positions</code>
                    <p>Posições ativas do scalping</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/scalping/history</code>
                    <p>Histórico do bot de scalping</p>
                </div>
            </div>
        </div>

        <!-- General API -->
        <div class="card mt-4">
            <div class="card-header bg-secondary text-white">
                <h5>🔧 General API</h5>
            </div>
            <div class="card-body">
                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/health</code>
                    <p>Health check geral do servidor</p>
                    <p class="text-muted">Response: { "mt5_connected": true/false, "status": "healthy" }</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/ping</code>
                    <p>Teste de conectividade simples</p>
                    <p class="text-muted">Response: "pong"</p>
                </div>

                <div class="endpoint">
                    <span class="method method-get">GET</span>
                    <code>/test-mlp</code>
                    <p>Teste de conectividade MLP</p>
                    <p class="text-muted">Response: Status do sistema MLP</p>
                </div>
            </div>
        </div>

        <!-- Integration Info -->
        <div class="card mt-4">
            <div class="card-header bg-dark text-white">
                <h5>🔗 Integration Notes</h5>
            </div>
            <div class="card-body">
                <h6>MCP Server (Porta 3000)</h6>
                <p>O servidor MCP em <code>http://localhost:3000</code> fornece interface conversacional para LLMs.</p>
                <ul>
                    <li><strong>Tools Available:</strong> 7 ferramentas funcionais</li>
                    <li><strong>Real Data:</strong> Conecta com MT5 em tempo real</li>
                    <li><strong>WebSockets:</strong> Suporte a conexões websocket</li>
                    <li><strong>Test Frontend:</strong> http://localhost:3000/test-frontend.html</li>
                </ul>

                <h6>Django Dashboard (Porta 5001)</h6>
                <p>Interface administrativa em <code>http://localhost:5001</code> com controle completo do sistema.</p>
            </div>
        </div>

        <hr class="mt-5">
        <footer class="text-center text-muted mt-4">
            <p>© 2025 MLP Trading System - API Documentation v1.0</p>
            <small>Sistema revolucionário de trading automatizado com IA</small>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@apidocs_bp.route('/apidocs')
@apidocs_bp.route('/docs')
@apidocs_bp.route('/api-docs')
def api_docs():
    """Página de documentação da API"""
    return render_template_string(API_DOCUMENTATION_HTML)

@apidocs_bp.route('/api/v1/endpoints')
def api_endpoints():
    """JSON com lista de endpoints disponíveis"""
    return {
        "message": "MLP Trading System API Endpoints",
        "version": "1.0",
        "base_url": "http://localhost:5000",
        "endpoints": {
            "health": [
                {"method": "GET", "path": "/health", "description": "Health check MT5"}
            ],
            "btcusd": [
                {"method": "GET", "path": "/btcusd/stats", "description": "Dados de mercado completos"},
                {"method": "GET", "path": "/btcusd/indicators/M1", "description": "Indicadores técnicos"},
                {"method": "GET", "path": "/btcusd/analysis/M1", "description": "Análise técnica"}
            ],
            "mlp": [
                {"method": "GET", "path": "/mlp/health", "description": "Health MLP"},
                {"method": "POST", "path": "/mlp/start", "description": "Iniciar bot"},
                {"method": "POST", "path": "/mlp/stop", "description": "Parar bot"},
                {"method": "GET", "path": "/mlp/status", "description": "Status bot"},
                {"method": "POST", "path": "/mlp/execute", "description": "Executar sinal"},
                {"method": "GET", "path": "/mlp/performance", "description": "Performance"},
                {"method": "GET", "path": "/mlp/positions", "description": "Posições abertas"},
                {"method": "GET", "path": "/mlp/history", "description": "Histórico análises"},
                {"method": "GET", "path": "/mlp/trades", "description": "Histórico trades"}
            ],
            "scalping": [
                {"method": "GET", "path": "/scalping/dashboard", "description": "Dashboard scalping"},
                {"method": "POST", "path": "/scalping/start", "description": "Iniciar scalping"},
                {"method": "POST", "path": "/scalping/stop", "description": "Parar scalping"},
                {"method": "GET", "path": "/scalping/status", "description": "Status scalping"},
                {"method": "GET", "path": "/scalping/positions", "description": "Posições scalping"},
                {"method": "GET", "path": "/scalping/history", "description": "Histórico scalping"}
            ],
            "bot_standalone": [
                {"method": "GET", "path": "/bot/health", "description": "Health check bot"},
                {"method": "POST", "path": "/bot/start", "description": "Iniciar bot trading"},
                {"method": "POST", "path": "/bot/stop", "description": "Parar bot trading"},
                {"method": "GET", "path": "/bot/mlp-status", "description": "Status detalhado bot MLP"},
                {"method": "POST", "path": "/bot/execute", "description": "Executar sinal BUY/SELL/HOLD"},
                {"method": "POST", "path": "/bot/analyze", "description": "Analisar mercado automaticamente"},
                {"method": "POST", "path": "/bot/train", "description": "Treinar modelo MLP"},
                {"method": "POST", "path": "/bot/emergency-close", "description": "Fechar posições emergência"},
                {"method": "GET", "path": "/bot/performance", "description": "Relatório performance"},
                {"method": "GET", "path": "/bot/positions", "description": "Posições ativas MT5"},
                {"method": "GET", "path": "/bot/market-data", "description": "Dados mercado tempo real"}
            ]
        },
        "mcp_server": {
            "url": "http://localhost:3000",
            "description": "MCP Server para integração com LLMs",
            "tools": [
                "get_market_data",
                "get_mlp_signal",
                "get_trade_history",
                "execute_trade",
                "get_performance",
                "get_portfolio",
                "get_bot_status"
            ]
        },
        "django_dashboard": {
            "url": "http://localhost:5001",
            "description": "Dashboard administrativo Django"
        }
    }
