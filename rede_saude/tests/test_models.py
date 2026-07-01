from django.core.exceptions import ValidationError
from django.test import TestCase

from rede_saude.models import UnidadeSaude


class UnidadeSaudeModelTests(TestCase):
    def test_cria_unidade_com_valores_obrigatorios(self):
        unidade = UnidadeSaude.objects.create(
            nome="Unidade Básica de Saúde Central",
            endereco="Rua das Flores, 100",
        )

        self.assertEqual(unidade.nome, "Unidade Básica de Saúde Central")
        self.assertEqual(unidade.endereco, "Rua das Flores, 100")
        self.assertIsNone(unidade.contato)
        self.assertTrue(unidade.ativo)

    def test_contato_pode_ser_nulo(self):
        unidade = UnidadeSaude(
            nome="Unidade de Teste",
            endereco="Avenida de Teste, 200",
            contato=None,
        )

        unidade.full_clean()

    def test_nome_e_obrigatorio(self):
        unidade = UnidadeSaude(nome="", endereco="Rua de Teste, 10")

        with self.assertRaises(ValidationError) as contexto:
            unidade.full_clean()

        self.assertIn("nome", contexto.exception.message_dict)

    def test_endereco_e_obrigatorio(self):
        unidade = UnidadeSaude(nome="Unidade de Teste", endereco="")

        with self.assertRaises(ValidationError) as contexto:
            unidade.full_clean()

        self.assertIn("endereco", contexto.exception.message_dict)

    def test_representacao_textual_utiliza_nome(self):
        unidade = UnidadeSaude(
            nome="Unidade de Referência",
            endereco="Rua de Referência, 50",
        )

        self.assertEqual(str(unidade), "Unidade de Referência")

