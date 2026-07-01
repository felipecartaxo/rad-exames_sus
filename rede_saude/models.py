from django.db import models
from django.utils.translation import gettext_lazy as _

from .validators import normalizar_cpf, validar_cpf


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


class Profissional(models.Model):
    nome = models.CharField(_("nome"), max_length=150)
    cpf = models.CharField(
        _("CPF"),
        max_length=11,
        unique=True,
        validators=[validar_cpf],
    )
    cargo = models.CharField(_("cargo"), max_length=100)
    especialidade = models.CharField(
        _("especialidade"),
        max_length=100,
        null=True,
        blank=True,
    )
    unidade = models.ForeignKey(
        UnidadeSaude,
        on_delete=models.PROTECT,
        related_name="profissionais",
        verbose_name=_("unidade de saúde"),
    )
    ativo = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("profissional")
        verbose_name_plural = _("profissionais")

    def clean_fields(self, exclude=None):
        self.cpf = normalizar_cpf(self.cpf)
        super().clean_fields(exclude=exclude)

    def save(self, *args, **kwargs):
        self.cpf = normalizar_cpf(self.cpf)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
