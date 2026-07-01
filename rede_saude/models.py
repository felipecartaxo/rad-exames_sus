from django.db import models
from django.utils.translation import gettext_lazy as _


class UnidadeSaude(models.Model):
    nome = models.CharField(_("nome"), max_length=150)
    endereco = models.CharField(_("endereço"), max_length=255)
    contato = models.CharField(
        _("contato"),
        max_length=100,
        null=True,
        blank=True,
    )
    ativo = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("unidade de saúde")
        verbose_name_plural = _("unidades de saúde")

    def __str__(self):
        return self.nome

