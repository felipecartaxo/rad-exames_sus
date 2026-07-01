from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from exames.models import Exame


class Notificacao(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="notificacoes",
        verbose_name=_("usuário"),
    )
    exame = models.OneToOneField(
        Exame,
        on_delete=models.PROTECT,
        related_name="notificacao_resultado",
        verbose_name=_("exame"),
    )
    mensagem = models.CharField(_("mensagem"), max_length=255)
    lida = models.BooleanField(_("lida"), default=False)

    class Meta:
        ordering = ("-pk",)
        verbose_name = _("notificação")
        verbose_name_plural = _("notificações")

    def clean(self):
        super().clean()
        if self.exame_id and self.usuario_id != self.exame.usuario_id:
            raise ValidationError(
                {"usuario": _("O usuário deve ser o proprietário do exame.")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.mensagem

