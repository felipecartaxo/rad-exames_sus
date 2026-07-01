from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExamesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "exames"
    verbose_name = _("Exames")

