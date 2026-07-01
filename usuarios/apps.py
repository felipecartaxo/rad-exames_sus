from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"
    verbose_name = _("Usuários")

