"""
Global views for MLP Trading System
Handles general functionality including API documentation
"""

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.template.loader import render_to_string

def api_docs_view(request: HttpRequest) -> HttpResponse:
    """
    API Documentation view for Django
    Renders comprehensive API documentation
    """
    return render(request, 'api_docs.html', {
        'title': 'MLP Trading System - API Documentation'
    })

def api_endpoints_view(request: HttpRequest) -> HttpResponse:
    """
    Returns JSON with all available API endpoints
    """
    endpoints_data = {
        "message": "MLP Trading System API Endpoints",
        "version": "1.0",
        "services": {
            "flask_api": {
                "url": "http://localhost:5000",
                "description": "API principal Flask - Sistema de trading",
                "endpoints": {
                    "health": "/health, /ping, /test-mlp",
                    "btcusd": "/btcusd/stats, /btcusd/indicators/M1, /btcusd/analysis/M1",
                    "mlp": "/mlp/health, /mlp/start, /mlp/stop, /mlp/status, /mlp/execute",
                    "scalping": "/scalping/dashboard, /scalping/start, /scalping/stop, /scalping/status",
                    "bot_standalone": "/bot/health, /bot/start, /bot/stop, /bot/mlp-status, /bot/execute"
                }
            },
            "django_dashboard": {
                "url": "http://localhost:8000",
                "description": "Dashboard administrativo Django",
                "endpoints": {
                    "admin": "/admin/",
                    "quant": "/quant/mlp, /quant/mlp/control/, /quant/mlp/dashboard/, /quant/daily-pnl/"
                }
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
            }
        }
    }

    import json
    return HttpResponse(
        json.dumps(endpoints_data, indent=2),
        content_type='application/json'
    )
