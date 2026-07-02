from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


TAMANHO_MAXIMO_DOCUMENTO_RESULTADO = 10 * 1024 * 1024


def validar_documento_resultado(arquivo):
    if Path(arquivo.name).suffix.lower() != ".pdf":
        raise ValidationError(
            _("Envie um documento no formato PDF."),
            code="extensao_invalida",
        )
    if arquivo.size > TAMANHO_MAXIMO_DOCUMENTO_RESULTADO:
        raise ValidationError(
            _("O documento deve possuir no máximo 10 MB."),
            code="arquivo_muito_grande",
        )
    tipo = getattr(arquivo, "content_type", None)
    if tipo and tipo != "application/pdf":
        raise ValidationError(
            _("O conteúdo enviado não é um PDF válido."),
            code="tipo_invalido",
        )

    posicao = arquivo.tell()
    assinatura = arquivo.read(5)
    arquivo.seek(posicao)
    if assinatura != b"%PDF-":
        raise ValidationError(
            _("O conteúdo enviado não é um PDF válido."),
            code="conteudo_invalido",
        )
