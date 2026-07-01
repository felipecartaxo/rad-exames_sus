import re

from django.contrib.auth.base_user import BaseUserManager


def normalizar_cpf(cpf):
    """Remove a formatação do CPF, preservando somente seus dígitos."""
    if cpf is None:
        return ""
    return re.sub(r"\D", "", str(cpf))


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, cpf):
        return self.get(**{self.model.USERNAME_FIELD: normalizar_cpf(cpf)})

    def create_user(self, cpf, nome, tipo, password=None, **extra_fields):
        cpf_normalizado = normalizar_cpf(cpf)
        if not cpf_normalizado:
            raise ValueError("O CPF é obrigatório.")
        if not nome or not nome.strip():
            raise ValueError("O nome é obrigatório.")
        if tipo not in self.model.Tipo.values:
            raise ValueError("O tipo de usuário é inválido.")

        usuario = self.model(
            cpf=cpf_normalizado,
            nome=nome.strip(),
            tipo=tipo,
            **extra_fields,
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, cpf, nome, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("O superusuário deve possuir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("O superusuário deve possuir is_superuser=True.")

        return self.create_user(
            cpf=cpf,
            nome=nome,
            tipo=self.model.Tipo.SERVIDOR,
            password=password,
            **extra_fields,
        )

