from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from exames.models import Agendamento
from rede_saude.models import UnidadeSaude


Usuario = get_user_model()


class AgendamentoModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Básica de Saúde Central",
            endereco="Rua das Flores, 100",
        )
        cls.data = timezone.make_aware(datetime(2026, 8, 10, 14, 30))

    def test_cria_agendamento_com_usuario_unidade_data_e_horario(self):
        agendamento = Agendamento.objects.create(
            usuario=self.usuario,
            unidade=self.unidade,
            data=self.data,
        )

        self.assertEqual(agendamento.usuario, self.usuario)
        self.assertEqual(agendamento.unidade, self.unidade)
        self.assertEqual(agendamento.data, self.data)
        self.assertEqual(agendamento.data.hour, 14)
        self.assertEqual(agendamento.data.minute, 30)

    def test_campos_obrigatorios_sao_validados(self):
        agendamento = Agendamento(usuario=None, unidade=None, data=None)

        with self.assertRaises(ValidationError) as contexto:
            agendamento.full_clean()

        self.assertEqual(
            {"usuario", "unidade", "data"},
            set(contexto.exception.message_dict),
        )

    def test_usuario_com_agendamento_nao_pode_ser_excluido(self):
        Agendamento.objects.create(
            usuario=self.usuario,
            unidade=self.unidade,
            data=self.data,
        )

        with self.assertRaises(ProtectedError):
            self.usuario.delete()

    def test_unidade_com_agendamento_nao_pode_ser_excluida(self):
        Agendamento.objects.create(
            usuario=self.usuario,
            unidade=self.unidade,
            data=self.data,
        )

        with self.assertRaises(ProtectedError):
            self.unidade.delete()

    def test_relacoes_reversas_listam_agendamentos(self):
        agendamento = Agendamento.objects.create(
            usuario=self.usuario,
            unidade=self.unidade,
            data=self.data,
        )

        self.assertSequenceEqual(self.usuario.agendamentos.all(), [agendamento])
        self.assertSequenceEqual(self.unidade.agendamentos.all(), [agendamento])

    def test_representacao_textual_identifica_usuario_e_data(self):
        agendamento = Agendamento(
            usuario=self.usuario,
            unidade=self.unidade,
            data=self.data,
        )

        representacao = str(agendamento)

        self.assertIn(self.usuario.nome, representacao)
        self.assertIn(str(self.data), representacao)

