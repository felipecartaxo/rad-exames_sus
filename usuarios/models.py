from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UsuarioManager, normalizar_cpf


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Tipo(models.TextChoices):
        CIDADAO = "CIDADAO", _("Cidadão")
        SERVIDOR = "SERVIDOR", _("Servidor")

    nome = models.CharField(_("nome"), max_length=150)
    cpf = models.CharField(_("CPF"), max_length=11, unique=True)
    tipo = models.CharField(_("tipo"), max_length=8, choices=Tipo.choices)
    is_staff = models.BooleanField(_("acesso à administração"), default=False)
    is_active = models.BooleanField(_("ativo"), default=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "cpf"
    REQUIRED_FIELDS = ["nome"]

    class Meta:
        verbose_name = _("usuário")
        verbose_name_plural = _("usuários")

    def clean(self):
        super().clean()
        self.cpf = normalizar_cpf(self.cpf)
        self.nome = self.nome.strip()

    def save(self, *args, **kwargs):
        self.cpf = normalizar_cpf(self.cpf)
        self.nome = self.nome.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

