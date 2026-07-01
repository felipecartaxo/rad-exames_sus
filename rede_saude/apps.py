from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RedeSaudeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rede_saude"
    verbose_name = _("Rede de saúde")

