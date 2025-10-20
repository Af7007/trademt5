from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class ScalpingSetfile(models.Model):
    """
    Modelo para armazenar configurações (setfiles) do Scalping Bot
    """
    # Identificação
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nome único para identificar o setfile"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Descrição do setfile e estratégia"
    )

    # Parâmetros do bot
    symbol = models.CharField(
        max_length=20,
        default="BTCUSDc",
        help_text="Símbolo para operar (ex: BTCUSDc, EURUSD)"
    )

    timeframe = models.IntegerField(
        default=5,
        choices=[
            (1, 'M1'),
            (5, 'M5'),
            (15, 'M15'),
            (30, 'M30'),
            (60, 'H1'),
            (240, 'H4'),
            (1440, 'D1'),
        ],
        help_text="Timeframe para análise (em minutos)"
    )

    confidence_threshold = models.FloatField(
        default=85.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Threshold de confiança mínimo para entrar em operação (0-100%)"
    )

    volume = models.FloatField(
        default=0.01,
        validators=[MinValueValidator(0.001)],
        help_text="Volume para cada operação (lotes)"
    )

    use_dynamic_risk = models.BooleanField(
        default=True,
        help_text="Usar gerenciamento de risco dinâmico"
    )

    # Parâmetros de risco
    max_positions = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Número máximo de posições simultâneas"
    )

    # Stop Loss options
    stop_loss_pct = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Stop Loss em porcentagem (%)"
    )

    stop_loss_usd = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
        help_text="Stop Loss em valor fixo (USD). Se preenchido, sobrescreve stop_loss_pct"
    )

    # Take Profit options
    take_profit_pct = models.FloatField(
        default=0.3,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text="Take Profit em porcentagem (%)"
    )

    take_profit_usd = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
        help_text="Take Profit em valor fixo (USD). Se preenchido, sobrescreve take_profit_pct"
    )

    max_daily_loss = models.FloatField(
        default=-50.0,
        validators=[MaxValueValidator(0.0)],
        help_text="Perda máxima diária permitida (valor negativo em USD)"
    )

    # Parâmetros de execução
    interval = models.IntegerField(
        default=60,
        validators=[MinValueValidator(5), MaxValueValidator(3600)],
        help_text="Intervalo entre ciclos de análise (segundos)"
    )

    # Indicadores técnicos
    rsi_period = models.IntegerField(
        default=14,
        validators=[MinValueValidator(5), MaxValueValidator(50)],
        help_text="Período para cálculo do RSI"
    )

    rsi_oversold = models.FloatField(
        default=30.0,
        validators=[MinValueValidator(10.0), MaxValueValidator(40.0)],
        help_text="Nível de RSI para sobrevendido"
    )

    rsi_overbought = models.FloatField(
        default=70.0,
        validators=[MinValueValidator(60.0), MaxValueValidator(90.0)],
        help_text="Nível de RSI para sobrecomprado"
    )

    sma_short_period = models.IntegerField(
        default=10,
        validators=[MinValueValidator(3), MaxValueValidator(50)],
        help_text="Período para SMA curta"
    )

    sma_long_period = models.IntegerField(
        default=20,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
        help_text="Período para SMA longa"
    )

    # Status e metadata
    is_active = models.BooleanField(
        default=True,
        help_text="Se este setfile está ativo para uso"
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Se este é o setfile padrão"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Data de criação do setfile"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última atualização do setfile"
    )

    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última vez que este setfile foi usado"
    )

    # Estatísticas de uso
    total_runs = models.IntegerField(
        default=0,
        help_text="Número de vezes que este setfile foi executado"
    )

    total_profit_loss = models.FloatField(
        default=0.0,
        help_text="P&L total acumulado usando este setfile"
    )

    class Meta:
        verbose_name = "Scalping Setfile"
        verbose_name_plural = "Scalping Setfiles"
        ordering = ['-is_default', '-last_used_at', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.symbol} - {self.get_timeframe_display()})"

    def save(self, *args, **kwargs):
        # Se este for marcado como default, desmarcar os outros
        if self.is_default:
            ScalpingSetfile.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def to_bot_config(self):
        """
        Converte o setfile para dicionário de configuração do bot
        """
        # Converter timeframe para constante do MT5
        timeframe_map = {
            1: 1,      # TIMEFRAME_M1
            5: 5,      # TIMEFRAME_M5
            15: 15,    # TIMEFRAME_M15
            30: 30,    # TIMEFRAME_M30
            60: 16385, # TIMEFRAME_H1
            240: 16386,# TIMEFRAME_H4 (corrigido de 16388)
            1440: 16408,# TIMEFRAME_D1
        }

        tf_value = timeframe_map.get(self.timeframe, 5)

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[Setfile {self.name}] Convertendo timeframe: {self.timeframe}min -> MT5={tf_value}")

        return {
            'symbol': self.symbol,
            'timeframe': tf_value,
            'confidence_threshold': self.confidence_threshold,
            'volume': self.volume,
            'use_dynamic_risk': self.use_dynamic_risk,
            'max_positions': self.max_positions,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'stop_loss_usd': self.stop_loss_usd,
            'take_profit_usd': self.take_profit_usd,
            'max_daily_loss': self.max_daily_loss,
            'interval': self.interval,
            'rsi_period': self.rsi_period,
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'sma_short_period': self.sma_short_period,
            'sma_long_period': self.sma_long_period,
        }

    def mark_as_used(self):
        """
        Marca o setfile como usado agora
        """
        self.last_used_at = timezone.now()
        self.total_runs += 1
        self.save(update_fields=['last_used_at', 'total_runs'])

    def update_profit_loss(self, pnl: float):
        """
        Atualiza o P&L acumulado do setfile
        """
        self.total_profit_loss += pnl
        self.save(update_fields=['total_profit_loss'])


class MLPAnalysis(models.Model):
    """
    Modelo para armazenar análises do modelo MLP
    """

    SIGNAL_CHOICES = [
        ('BUY', 'Compra'),
        ('SELL', 'Venda'),
        ('HOLD', 'Espera'),
    ]

    # Identificação da análise
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp da análise"
    )
    symbol = models.CharField(
        max_length=20,
        default="BTCUSDc",
        help_text="Símbolo analisado"
    )
    timeframe = models.CharField(
        max_length=10,
        default="M1",
        help_text="Timeframe da análise (M1, M5, H1, etc)"
    )

    # Resultado da análise
    signal = models.CharField(
        max_length=4,
        choices=SIGNAL_CHOICES,
        help_text="Sinal gerado pelo modelo"
    )
    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confiança da predição (0-1)"
    )

    # Metadados do modelo
    model_version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Versão do modelo usada"
    )

    # Dados técnicos analisados
    rsi = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True
    )
    macd_signal = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    bb_upper = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    bb_lower = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    sma_20 = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    sma_50 = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )

    # Contexto de mercado no momento
    price_open = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    price_high = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    price_low = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    price_close = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True
    )
    volume = models.PositiveIntegerField(null=True, blank=True)

    # Dados adicionais em JSON (usando TextField para SQLite)
    market_conditions = models.TextField(
        blank=True,
        null=True,
        help_text="Condições de mercado adicionais (JSON)"
    )
    technical_signals = models.TextField(
        blank=True,
        null=True,
        help_text="Sinais técnicos identificados (JSON)"
    )

    class Meta:
        verbose_name = "MLP Analysis"
        verbose_name_plural = "MLP Analyses"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['signal', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.signal} ({self.confidence:.2f}) - {self.timestamp}"


class MLPTrade(models.Model):
    """
    Modelo para armazenar trades executados pelo bot MLP
    """

    TRADE_TYPES = [
        ('BUY', 'Compra'),
        ('SELL', 'Venda'),
    ]

    EXIT_REASONS = [
        ('TP', 'Take Profit'),
        ('SL', 'Stop Loss'),
        ('MANUAL', 'Fechamento Manual'),
        ('EMERGENCY', 'Fechamento Emergencial'),
        ('CLOSE', 'Fechamento Normal'),
    ]

    # Trade básico
    ticket = models.PositiveIntegerField(
        unique=True,
        help_text="Ticket da ordem MT5"
    )
    symbol = models.CharField(
        max_length=20,
        help_text="Símbolo negociado"
    )
    type = models.CharField(
        max_length=4,
        choices=TRADE_TYPES,
        help_text="Tipo da posição"
    )
    volume = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        validators=[MinValueValidator(0.0001)]
    )

    # Análise que originou o trade
    analysis = models.ForeignKey(
        MLPAnalysis,
        on_delete=models.CASCADE,
        related_name='trades',
        help_text="Análise que gerou este trade"
    )

    # Preços de execução
    entry_price = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        help_text="Preço de entrada"
    )
    sl_price = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Preço do Stop Loss"
    )
    tp_price = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Preço do Take Profit"
    )

    # Dados de fechamento
    exit_price = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Preço de saída"
    )
    exit_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento do fechamento"
    )
    exit_reason = models.CharField(
        max_length=10,
        choices=EXIT_REASONS,
        null=True,
        blank=True,
        help_text="Razão do fechamento"
    )

    # Resultados
    profit = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Lucro/prejuízo da operação"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Momento da criação"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última atualização"
    )

    class Meta:
        verbose_name = "MLP Trade"
        verbose_name_plural = "MLP Trades"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket']),
            models.Index(fields=['symbol', 'created_at']),
            models.Index(fields=['analysis']),
        ]

    def __str__(self):
        profit_str = f" (${self.profit})" if self.profit else ""
        return f"{self.symbol} {self.type}@{self.entry_price}{profit_str}"

    @property
    def duration(self):
        """Duração da posição em horas"""
        if self.exit_time and self.created_at:
            return (self.exit_time - self.created_at).total_seconds() / 3600
        return None

    @property
    def is_profitable(self):
        """Verifica se o trade foi lucrativo"""
        return self.profit is not None and self.profit > 0


class MLPDailyStats(models.Model):
    """
    Estatísticas diárias do bot MLP
    """

    date = models.DateField(
        unique=True,
        help_text="Data das estatísticas"
    )

    # Trades do dia
    total_trades = models.PositiveIntegerField(
        default=0,
        help_text="Total de trades executados"
    )
    winning_trades = models.PositiveIntegerField(
        default=0,
        help_text="Trades vencedores"
    )
    losing_trades = models.PositiveIntegerField(
        default=0,
        help_text="Trades perdedores"
    )

    # Análises do dia
    total_analyses = models.PositiveIntegerField(
        default=0,
        help_text="Total de análises realizadas"
    )
    buy_signals = models.PositiveIntegerField(
        default=0,
        help_text="Sinais de compra"
    )
    sell_signals = models.PositiveIntegerField(
        default=0,
        help_text="Sinais de venda"
    )
    hold_signals = models.PositiveIntegerField(
        default=0,
        help_text="Sinais de espera"
    )

    # P&L
    total_profit = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0.0,
        help_text="Lucro total do dia"
    )
    gross_profit = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0.0,
        help_text="Lucro bruto (somente vencedores)"
    )
    gross_loss = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=0.0,
        help_text="Prejuízo bruto (somente perdedores)"
    )

    # Métricas calculadas
    win_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Taxa de vitória (%)"
    )
    avg_profit = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Lucro médio por trade"
    )
    avg_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Confiança média"
    )

    # Máximas e mínimas
    max_drawdown = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Drawdown máximo (%)"
    )
    largest_win = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Maior vitória"
    )
    largest_loss = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Maior perda"
    )

    # Metadata
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última atualização"
    )

    class Meta:
        verbose_name = "MLP Daily Stats"
        verbose_name_plural = "MLP Daily Stats"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.total_trades} trades, {self.total_profit:.2f}"

    def calculate_metrics(self):
        """Calcula métricas automaticamente"""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades * 100).quantize(Decimal('0.01'))
        if self.total_trades > 0:
            self.avg_profit = (self.total_profit / self.total_trades).quantize(Decimal('0.0001'))

        # TODO: Calcular métricas mais avançadas
        # - Drawdown
        # - Largest win/loss
        # - Sharpe ratio
        # - Confidence correlations etc
