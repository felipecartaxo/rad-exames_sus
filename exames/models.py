from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from rede_saude.models import UnidadeSaude


class Agendamento(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        verbose_name=_("usuário"),
    )
    unidade = models.ForeignKey(
        UnidadeSaude,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        verbose_name=_("unidade de saúde"),
    )
    data = models.DateTimeField(_("data e horário"))

    class Meta:
        verbose_name = _("agendamento")
        verbose_name_plural = _("agendamentos")

    def __str__(self):
        return _("Agendamento de %(usuario)s em %(data)s") % {
            "usuario": self.usuario,
            "data": self.data,
        }

