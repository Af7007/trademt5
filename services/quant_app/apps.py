from django.apps import AppConfig


class QuantAppConfig(AppConfig):
    """
    Configuração do app Django para sistema MLP
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.quant_app'
    verbose_name = 'Sistema MLP'
