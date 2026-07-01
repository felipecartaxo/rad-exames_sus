from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from rede_saude.models import Profissional, UnidadeSaude


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


class Exame(models.Model):
    class Status(models.TextChoices):
        AGENDADO = "AGENDADO", _("Agendado")
        AGUARDANDO_CONFIRMACAO = (
            "AGUARDANDO_CONFIRMACAO",
            _("Aguardando confirmação"),
        )
        CONFIRMADO = "CONFIRMADO", _("Confirmado")
        REALIZADO = "REALIZADO", _("Realizado")
        EM_ANALISE = "EM_ANALISE", _("Em análise")
        RESULTADO_DISPONIVEL = "RESULTADO_DISPONIVEL", _("Resultado disponível")
        CANCELADO = "CANCELADO", _("Cancelado")

    tipo = models.CharField(_("tipo"), max_length=150)
    data = models.DateTimeField(_("data e horário"))
    status = models.CharField(_("status"), max_length=23, choices=Status.choices)
    resultado = models.TextField(_("resultado"), blank=True, default="")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="exames",
        verbose_name=_("usuário"),
    )
    unidade = models.ForeignKey(
        UnidadeSaude,
        on_delete=models.PROTECT,
        related_name="exames",
        verbose_name=_("unidade de saúde"),
    )
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.PROTECT,
        related_name="exames",
        verbose_name=_("profissional"),
    )
    agendamento = models.ForeignKey(
        Agendamento,
        on_delete=models.PROTECT,
        related_name="exames",
        verbose_name=_("agendamento"),
    )

    class Meta:
        verbose_name = _("exame")
        verbose_name_plural = _("exames")

    def clean(self):
        super().clean()
        erros = {}

        if self.agendamento_id:
            if self.usuario_id != self.agendamento.usuario_id:
                erros["usuario"] = _(
                    "O usuário deve ser o mesmo usuário do agendamento."
                )
            if self.unidade_id != self.agendamento.unidade_id:
                erros["unidade"] = _(
                    "A unidade deve ser a mesma unidade do agendamento."
                )

        if self.pk:
            status_anterior = type(self).objects.filter(pk=self.pk).values_list(
                "status",
                flat=True,
            ).first()
            if status_anterior and status_anterior != self.status:
                from .services import validar_transicao_status

                try:
                    validar_transicao_status(status_anterior, self.status)
                except ValidationError as erro:
                    erros["status"] = erro.messages[0]

        if erros:
            raise ValidationError(erros)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return _("%(tipo)s de %(usuario)s") % {
            "tipo": self.tipo,
            "usuario": self.usuario,
        }
