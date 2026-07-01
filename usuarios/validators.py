from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .managers import normalizar_cpf


def _calcular_digito(cpf_parcial, peso_inicial):
    soma = sum(
        int(digito) * peso
        for digito, peso in zip(
            cpf_parcial,
            range(peso_inicial, 1, -1),
            strict=True,
        )
    )
    resto = 11 - (soma % 11)
    return "0" if resto >= 10 else str(resto)


def validar_cpf(cpf):
    cpf_normalizado = normalizar_cpf(cpf)
    cpf_invalido = (
        len(cpf_normalizado) != 11
        or len(set(cpf_normalizado)) == 1
    )

    if not cpf_invalido:
        primeiro_digito = _calcular_digito(cpf_normalizado[:9], 10)
        segundo_digito = _calcular_digito(
            cpf_normalizado[:9] + primeiro_digito,
            11,
        )
        cpf_invalido = cpf_normalizado[-2:] != primeiro_digito + segundo_digito

    if cpf_invalido:
        raise ValidationError(
            _("Informe um CPF válido."),
            code="cpf_invalido",
        )

