from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from usuarios.models import Usuario

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


class Profissional(Usuario):
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

    class Meta:
        verbose_name = _("profissional")
        verbose_name_plural = _("profissionais")

    def clean_fields(self, exclude=None):
        self.cpf = normalizar_cpf(self.cpf)
        self.tipo = Usuario.Tipo.PROFISSIONAL
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        try:
            validar_cpf(self.cpf)
        except ValidationError as erro:
            raise ValidationError({"cpf": erro.messages}) from erro
        self.tipo = Usuario.Tipo.PROFISSIONAL

    def save(self, *args, **kwargs):
        self.tipo = Usuario.Tipo.PROFISSIONAL
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
