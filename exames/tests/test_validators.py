from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from exames.validators import (
    TAMANHO_MAXIMO_DOCUMENTO_RESULTADO,
    validar_documento_resultado,
)


class DocumentoResultadoValidatorTests(SimpleTestCase):
    def test_rejeita_pdf_com_conteudo_falsificado(self):
        arquivo = SimpleUploadedFile(
            "resultado.pdf",
            b"conteudo que nao e PDF",
            content_type="application/pdf",
        )

        with self.assertRaises(ValidationError):
            validar_documento_resultado(arquivo)

    def test_rejeita_pdf_maior_que_dez_megabytes(self):
        arquivo = SimpleUploadedFile(
            "resultado.pdf",
            b"%PDF-" + b"0" * TAMANHO_MAXIMO_DOCUMENTO_RESULTADO,
            content_type="application/pdf",
        )

        with self.assertRaises(ValidationError):
            validar_documento_resultado(arquivo)
