"""
URLs para o app Quant no projeto local
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Páginas HTML
    mlp_dashboard,
    mlp_analyses,
    mlp_trades,
    mlp_control,

    # APIs MLP (com CSRF exempt)
    mlp_analytics_api,
    mlp_status,
    mlp_start,
    mlp_stop,
    mlp_analyze,
    mlp_execute,
    mlp_health,
    mlp_history,
    mlp_trades_api,
    mlp_get_analysis,

    # Controle de bot
    mlp_bot_start,
    mlp_bot_stop,

    # Bot automático
    mlp_bot_auto_start,
    mlp_bot_auto_stop,
    mlp_bot_status,

    # Analytics legado
    mlp_analytics,

    # Real-time dashboard APIs
    mlp_api_logs,
    mlp_api_analysis_latest,
    mlp_api_status,
)

# Router para ViewSets (se houver)
try:
    router = DefaultRouter()
except ImportError:
    router = None

app_name = 'quant'

urlpatterns = [
    # URLs do sistema MLP (Interface)
    path('mlp/', mlp_dashboard, name='mlp_dashboard'),
    path('mlp/analyses/', mlp_analyses, name='mlp_analyses'),
    path('mlp/trades/', mlp_trades, name='mlp_trades'),
    path('mlp/control/', mlp_control, name='mlp_control'),

    # APIs do sistema MLP (Para gráficos AJAX - Legacy)
    path('api/mlp/analytics/', mlp_analytics_api, name='mlp_analytics_api'),
    path('api/mlp/status/', mlp_status, name='mlp_status_api'),
    path('api/mlp/bot/start/', mlp_bot_start, name='mlp_bot_start_api'),
    path('api/mlp/bot/stop/', mlp_bot_stop, name='mlp_bot_stop_api'),

    # ========================
    # NOVOS ENDPOINTS MLP PYTHON (porta 5002)
    # ========================

    # POST endpoints (CSRF exempt)
    path('mlp/analyze/', mlp_analyze, name='mlp_analyze_api'),
    path('mlp/execute/', mlp_execute, name='mlp_execute_api'),
    path('mlp/start/', mlp_start, name='mlp_start_api'),
    path('mlp/stop/', mlp_stop, name='mlp_stop_api'),

    # Bot automático
    path('mlp/bot/start/', mlp_bot_auto_start, name='mlp_bot_auto_start'),
    path('mlp/bot/stop/', mlp_bot_auto_stop, name='mlp_bot_auto_stop'),

    # GET endpoints
    path('mlp/analytics/', mlp_analytics, name='mlp_analytics_new_api'),
    path('mlp/get-analysis/', mlp_get_analysis, name='mlp_get_analysis_api'),
    path('mlp/health/', mlp_health, name='mlp_health_api'),
    path('mlp/history/', mlp_history, name='mlp_history_api'),
    path('mlp/trades/', mlp_trades_api, name='mlp_trades_new_api'),
    path('mlp/bot/status/', mlp_bot_status, name='mlp_bot_status'),

    # Real-time dashboard APIs
    path('mlp/api/logs/', mlp_api_logs, name='mlp_api_logs'),
    path('mlp/api/analysis/latest/', mlp_api_analysis_latest, name='mlp_api_analysis_latest'),
    path('mlp/api/status/', mlp_api_status, name='mlp_api_status'),

    # URLs originais (compatibilidade)
    path('', include(router.urls)) if router else path('', include('.')),
]
