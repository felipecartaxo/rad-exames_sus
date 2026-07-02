from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from exames.models import Exame


class Notificacao(models.Model):
    class TipoEvento(models.TextChoices):
        ATRIBUICAO = "ATRIBUICAO", _("Exame atribuído")
        RESULTADO_DISPONIVEL = (
            "RESULTADO_DISPONIVEL",
            _("Resultado disponível"),
        )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="notificacoes",
        verbose_name=_("usuário"),
    )
    exame = models.ForeignKey(
        Exame,
        on_delete=models.PROTECT,
        related_name="notificacoes",
        verbose_name=_("exame"),
    )
    tipo = models.CharField(
        _("tipo de evento"),
        max_length=30,
        choices=TipoEvento.choices,
        default=TipoEvento.RESULTADO_DISPONIVEL,
    )
    mensagem = models.CharField(_("mensagem"), max_length=255)
    lida = models.BooleanField(_("lida"), default=False)

    class Meta:
        ordering = ("-pk",)
        verbose_name = _("notificação")
        verbose_name_plural = _("notificações")
        constraints = [
            models.UniqueConstraint(
                fields=("exame", "usuario", "tipo"),
                name="notificacao_evento_destinatario_unico",
            )
        ]

    def clean(self):
        super().clean()
        if not self.exame_id:
            return
        destinatario = self.exame.usuario_id
        mensagem = _("O usuário deve ser o proprietário do exame.")
        if self.tipo == self.TipoEvento.ATRIBUICAO:
            destinatario = self.exame.profissional_id
            mensagem = _("O usuário deve ser o profissional responsável.")
        if self.usuario_id != destinatario:
            raise ValidationError({"usuario": mensagem})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.mensagem
