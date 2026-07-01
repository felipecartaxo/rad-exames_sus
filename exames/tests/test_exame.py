from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from exames.models import Agendamento, Exame
from exames.services import (
    TRANSICOES_STATUS,
    transicionar_status,
    validar_transicao_status,
)
from rede_saude.models import Profissional, UnidadeSaude


Usuario = get_user_model()


class ExameTestMixin:
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.outro_usuario = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Outra Cidadã",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua das Flores, 100",
        )
        cls.outra_unidade = UnidadeSaude.objects.create(
            nome="Unidade Norte",
            endereco="Avenida Norte, 200",
        )
        cls.profissional = Profissional.objects.create(
            nome="Profissional de Teste",
            cpf="12345678909",
            cargo="Médica",
            unidade=cls.outra_unidade,
        )
        cls.data = timezone.make_aware(datetime(2026, 8, 10, 14, 30))
        cls.agendamento = Agendamento.objects.create(
            usuario=cls.usuario,
            unidade=cls.unidade,
            data=cls.data,
        )

    def criar_exame(self, **alteracoes):
        dados = {
            "tipo": "Hemograma",
            "data": self.data,
            "status": Exame.Status.AGENDADO,
            "usuario": self.usuario,
            "unidade": self.unidade,
            "profissional": self.profissional,
            "agendamento": self.agendamento,
        }
        dados.update(alteracoes)
        return Exame.objects.create(**dados)


class ExameModelTests(ExameTestMixin, TestCase):
    def test_cria_exame_com_campos_e_relacoes_obrigatorios(self):
        exame = self.criar_exame()

        self.assertEqual(exame.tipo, "Hemograma")
        self.assertEqual(exame.data, self.data)
        self.assertEqual(exame.status, Exame.Status.AGENDADO)
        self.assertEqual(exame.resultado, "")
        self.assertEqual(exame.agendamento, self.agendamento)

    def test_resultado_nao_e_nulo_e_pode_iniciar_vazio(self):
        campo = Exame._meta.get_field("resultado")

        self.assertFalse(campo.null)
        self.assertTrue(campo.blank)
        self.assertEqual(campo.default, "")

    def test_status_possui_somente_valores_autorizados(self):
        self.assertEqual(
            set(Exame.Status.values),
            {
                "AGENDADO",
                "AGUARDANDO_CONFIRMACAO",
                "CONFIRMADO",
                "REALIZADO",
                "EM_ANALISE",
                "RESULTADO_DISPONIVEL",
                "CANCELADO",
            },
        )

    def test_rejeita_usuario_diferente_do_agendamento(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_exame(usuario=self.outro_usuario)

        self.assertIn("usuario", contexto.exception.message_dict)

    def test_rejeita_unidade_diferente_do_agendamento(self):
        with self.assertRaises(ValidationError) as contexto:
            self.criar_exame(unidade=self.outra_unidade)

        self.assertIn("unidade", contexto.exception.message_dict)

    def test_nao_impoe_unidade_do_profissional_igual_a_do_exame(self):
        exame = self.criar_exame()

        self.assertNotEqual(exame.profissional.unidade, exame.unidade)

    def test_relacoes_protegem_historico_contra_exclusao(self):
        self.criar_exame()

        for objeto in (
            self.usuario,
            self.unidade,
            self.profissional,
            self.agendamento,
        ):
            with self.subTest(modelo=type(objeto).__name__):
                with self.assertRaises(ProtectedError):
                    objeto.delete()

    def test_representacao_textual_identifica_tipo_e_usuario(self):
        exame = self.criar_exame()

        self.assertIn(exame.tipo, str(exame))
        self.assertIn(self.usuario.nome, str(exame))


class FluxoStatusTests(ExameTestMixin, TestCase):
    def test_mapa_contem_exatamente_as_transicoes_aprovadas(self):
        esperado = {
            Exame.Status.AGENDADO: {
                Exame.Status.AGUARDANDO_CONFIRMACAO,
                Exame.Status.CANCELADO,
            },
            Exame.Status.AGUARDANDO_CONFIRMACAO: {
                Exame.Status.CONFIRMADO,
                Exame.Status.CANCELADO,
            },
            Exame.Status.CONFIRMADO: {
                Exame.Status.REALIZADO,
                Exame.Status.CANCELADO,
            },
            Exame.Status.REALIZADO: {Exame.Status.EM_ANALISE},
            Exame.Status.EM_ANALISE: {Exame.Status.RESULTADO_DISPONIVEL},
            Exame.Status.RESULTADO_DISPONIVEL: set(),
            Exame.Status.CANCELADO: set(),
        }

        self.assertEqual(TRANSICOES_STATUS, esperado)

    def test_todas_as_transicoes_aprovadas_sao_aceitas(self):
        for status_atual, proximos_status in TRANSICOES_STATUS.items():
            for novo_status in proximos_status:
                with self.subTest(atual=status_atual, novo=novo_status):
                    validar_transicao_status(status_atual, novo_status)

    def test_transicoes_nao_listadas_sao_rejeitadas(self):
        for status_atual in Exame.Status.values:
            for novo_status in Exame.Status.values:
                if novo_status in TRANSICOES_STATUS[status_atual]:
                    continue
                with self.subTest(atual=status_atual, novo=novo_status):
                    with self.assertRaises(ValidationError):
                        validar_transicao_status(status_atual, novo_status)

    def test_servico_persiste_transicao_valida(self):
        exame = self.criar_exame()

        atualizado = transicionar_status(
            exame,
            Exame.Status.AGUARDANDO_CONFIRMACAO,
        )

        exame.refresh_from_db()
        self.assertEqual(atualizado.status, Exame.Status.AGUARDANDO_CONFIRMACAO)
        self.assertEqual(exame.status, Exame.Status.AGUARDANDO_CONFIRMACAO)

    def test_modelo_impede_alteracao_direta_com_transicao_invalida(self):
        exame = self.criar_exame()
        exame.status = Exame.Status.RESULTADO_DISPONIVEL

        with self.assertRaises(ValidationError):
            exame.save()

        exame.refresh_from_db()
        self.assertEqual(exame.status, Exame.Status.AGENDADO)

    def test_servico_rejeita_exame_nao_persistido(self):
        exame = Exame(status=Exame.Status.AGENDADO)

        with self.assertRaises(ValidationError):
            transicionar_status(exame, Exame.Status.CANCELADO)

