from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from rede_saude.models import Profissional, UnidadeSaude


class ProfissionalModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Básica de Saúde Central",
            endereco="Rua das Flores, 100",
        )

    def test_cria_profissional_com_campos_obrigatorios(self):
        profissional = Profissional.objects.create(
            nome="Ana Souza",
            cpf="529.982.247-25",
            password="hash-de-teste",
            cargo="Médica",
            unidade=self.unidade,
        )

        self.assertEqual(profissional.cpf, "52998224725")
        self.assertEqual(profissional.unidade, self.unidade)
        self.assertIsNone(profissional.especialidade)
        self.assertTrue(profissional.is_active)
        self.assertEqual(profissional.tipo, "PROFISSIONAL")

    def test_cpf_formatado_e_normalizado_antes_da_validacao(self):
        profissional = Profissional(
            nome="Ana Souza",
            cpf="529.982.247-25",
            password="hash-de-teste",
            cargo="Médica",
            unidade=self.unidade,
        )

        profissional.full_clean()

        self.assertEqual(profissional.cpf, "52998224725")

    def test_cpf_com_digitos_verificadores_invalidos_e_rejeitado(self):
        profissional = Profissional(
            nome="Ana Souza",
            cpf="529.982.247-24",
            password="hash-de-teste",
            cargo="Médica",
            unidade=self.unidade,
        )

        with self.assertRaises(ValidationError) as contexto:
            profissional.full_clean()

        self.assertIn("cpf", contexto.exception.message_dict)

    def test_cpf_repetido_e_rejeitado(self):
        Profissional.objects.create(
            nome="Ana Souza",
            cpf="52998224725",
            password="hash-de-teste",
            cargo="Médica",
            unidade=self.unidade,
        )
        duplicado = Profissional(
            nome="Outra Pessoa",
            cpf="529.982.247-25",
            password="hash-de-teste",
            cargo="Psicóloga",
            unidade=self.unidade,
        )

        with self.assertRaises(ValidationError) as contexto:
            duplicado.full_clean()

        self.assertIn("cpf", contexto.exception.message_dict)

    def test_especialidade_pode_ser_nula(self):
        profissional = Profissional(
            nome="Carlos Lima",
            cpf="111.444.777-35",
            password="hash-de-teste",
            cargo="Fisioterapeuta",
            especialidade=None,
            unidade=self.unidade,
        )

        profissional.full_clean()

    def test_campos_obrigatorios_sao_validados(self):
        profissional = Profissional(
            nome="",
            cpf="",
            password="",
            cargo="",
            unidade=None,
        )

        with self.assertRaises(ValidationError) as contexto:
            profissional.full_clean()

        self.assertEqual(
            {"password", "nome", "cpf", "cargo", "unidade"},
            set(contexto.exception.message_dict),
        )

    def test_unidade_com_profissional_nao_pode_ser_excluida(self):
        Profissional.objects.create(
            nome="Ana Souza",
            cpf="52998224725",
            password="hash-de-teste",
            cargo="Médica",
            unidade=self.unidade,
        )

        with self.assertRaises(ProtectedError):
            self.unidade.delete()

    def test_relacao_reversa_lista_profissionais_da_unidade(self):
        profissional = Profissional.objects.create(
            nome="Ana Souza",
            cpf="52998224725",
            password="hash-de-teste",
            cargo="Médica",
            unidade=self.unidade,
        )

        self.assertSequenceEqual(
            self.unidade.profissionais.all(),
            [profissional],
        )

    def test_representacao_textual_utiliza_nome(self):
        profissional = Profissional(
            nome="Ana Souza",
            cpf="52998224725",
            password="hash-de-teste",
            cargo="Médica",
            unidade=self.unidade,
        )

        self.assertEqual(str(profissional), "Ana Souza")
