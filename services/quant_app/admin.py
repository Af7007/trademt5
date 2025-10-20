from django.contrib import admin
from django.utils.html import format_html
from .models import ScalpingSetfile, MLPAnalysis, MLPTrade, MLPDailyStats


@admin.register(ScalpingSetfile)
class ScalpingSetfileAdmin(admin.ModelAdmin):
    """
    Admin para gerenciar Scalping Setfiles
    """
    list_display = [
        'name',
        'symbol',
        'timeframe',
        'confidence_threshold',
        'volume',
        'is_active',
        'is_default',
        'total_runs',
        'total_profit_loss',
        'last_used_at',
    ]

    list_filter = [
        'is_active',
        'is_default',
        'symbol',
        'timeframe',
        'created_at',
    ]

    search_fields = [
        'name',
        'description',
        'symbol',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'last_used_at',
        'total_runs',
        'total_profit_loss',
    ]

    fieldsets = (
        ('Identificação', {
            'fields': ('name', 'description', 'is_active', 'is_default')
        }),
        ('Parâmetros do Bot', {
            'fields': (
                'symbol',
                'timeframe',
                'confidence_threshold',
                'volume',
                'use_dynamic_risk',
                'interval',
            )
        }),
        ('Gerenciamento de Risco', {
            'fields': (
                'max_positions',
                ('stop_loss_pct', 'stop_loss_usd'),
                ('take_profit_pct', 'take_profit_usd'),
                'max_daily_loss',
            )
        }),
        ('Indicadores Técnicos', {
            'fields': (
                'rsi_period',
                'rsi_oversold',
                'rsi_overbought',
                'sma_short_period',
                'sma_long_period',
            )
        }),
        ('Estatísticas', {
            'fields': (
                'total_runs',
                'total_profit_loss',
                'last_used_at',
                'created_at',
                'updated_at',
            )
        }),
    )

    actions = ['set_as_default', 'activate_setfiles', 'deactivate_setfiles']

    def set_as_default(self, request, queryset):
        """Ação para definir um setfile como padrão"""
        if queryset.count() != 1:
            self.message_user(request, "Selecione apenas um setfile.", level='ERROR')
            return

        setfile = queryset.first()
        ScalpingSetfile.objects.filter(is_default=True).update(is_default=False)
        setfile.is_default = True
        setfile.save()

        self.message_user(request, f'Setfile "{setfile.name}" definido como padrão.')

    set_as_default.short_description = "Definir como padrão"

    def activate_setfiles(self, request, queryset):
        """Ação para ativar setfiles"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} setfile(s) ativado(s).')

    activate_setfiles.short_description = "Ativar setfiles selecionados"

    def deactivate_setfiles(self, request, queryset):
        """Ação para desativar setfiles"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} setfile(s) desativado(s).')

    deactivate_setfiles.short_description = "Desativar setfiles selecionados"


@admin.register(MLPAnalysis)
class MLPAnalysisAdmin(admin.ModelAdmin):
    """
    Admin para visualizar análises MLP
    """
    list_display = [
        'timestamp',
        'symbol',
        'signal_colored',
        'confidence_colored',
        'rsi',
        'sma_20',
        'sma_50',
        'model_version'
    ]
    list_filter = [
        'signal',
        'symbol',
        'timeframe',
        'timestamp',
        'model_version'
    ]
    search_fields = [
        'symbol',
        'signal',
        'model_version'
    ]
    readonly_fields = [
        'timestamp',
        'market_conditions',
        'technical_signals'
    ]
    ordering = ('-timestamp',)

    def signal_colored(self, obj):
        colors = {
            'BUY': 'green',
            'SELL': 'red',
            'HOLD': 'orange'
        }
        color = colors.get(obj.signal, 'black')
        return format_html(f'<b style="color: {color};">{obj.signal}</b>')
    signal_colored.short_description = 'Sinal'

    def confidence_colored(self, obj):
        if obj.confidence >= 0.8:
            color = 'green'
        elif obj.confidence >= 0.6:
            color = 'orange'
        else:
            color = 'red'
        return format_html(f'<b style="color: {color};">{obj.confidence:.2f}</b>')
    confidence_colored.short_description = 'Confiança'


@admin.register(MLPTrade)
class MLPTradeAdmin(admin.ModelAdmin):
    """
    Admin para visualizar trades MLP
    """
    list_display = [
        'ticket',
        'symbol',
        'type',
        'entry_price',
        'exit_price',
        'profit_colored',
        'duration_display',
        'exit_reason',
        'analysis_link'
    ]
    list_filter = [
        'symbol',
        'type',
        'exit_reason',
        'created_at'
    ]
    search_fields = [
        'ticket',
        'symbol'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'analysis'
    ]
    ordering = ('-created_at',)

    def profit_colored(self, obj):
        if obj.profit is None:
            return '-'
        if obj.profit > 0:
            color = 'green'
        else:
            color = 'red'
        return format_html(f'<b style="color: {color};">${obj.profit:.2f}</b>')
    profit_colored.short_description = 'Lucro'

    def duration_display(self, obj):
        if obj.duration is None:
            return '-'
        return f"{obj.duration:.2f}h"
    duration_display.short_description = 'Duração'

    def analysis_link(self, obj):
        url = f'/admin/quant/mlpanalysis/{obj.analysis.id}/change/'
        return format_html(f'<a href="{url}" target="_blank">Ver Análise</a>')
    analysis_link.short_description = 'Análise'


@admin.register(MLPDailyStats)
class MLPDailyStatsAdmin(admin.ModelAdmin):
    """
    Admin para estatísticas diárias MLP
    """
    list_display = [
        'date',
        'total_trades',
        'total_analyses',
        'win_rate_display',
        'total_profit_colored',
        'buy_signals',
        'sell_signals'
    ]
    list_filter = [
        'date'
    ]
    readonly_fields = [
        'updated_at'
    ]
    ordering = ('-date',)

    def win_rate_display(self, obj):
        if obj.win_rate is None:
            return '-'
        return f"{obj.win_rate}%"
    win_rate_display.short_description = 'Win Rate'

    def total_profit_colored(self, obj):
        if obj.total_profit == 0:
            return '$0.00'
        color = 'green' if obj.total_profit > 0 else 'red'
        return format_html(f'<b style="color: {color};">${obj.total_profit:.2f}</b>')
    total_profit_colored.short_description = 'Lucro Total'
