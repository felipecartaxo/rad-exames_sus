from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exames.forms import CriacaoAgendamentoExameForm
from exames.models import Agendamento, Exame
from exames.services import criar_agendamento_exame
from notificacoes.models import Notificacao
from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


class CriacaoAgendamentoExameViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã Ativa",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.cidadao_inativo = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Cidadã Inativa",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
            is_active=False,
        )
        cls.servidor = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Servidor Autorizado",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.servidor.user_permissions.add(
            Permission.objects.get(codename="add_agendamento"),
            Permission.objects.get(codename="add_exame"),
        )
        cls.servidor_sem_permissao = Usuario.objects.create_user(
            cpf="98765432100",
            nome="Servidor sem Permissão",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Ativa",
            endereco="Rua Principal, 10",
        )
        cls.outra_unidade = UnidadeSaude.objects.create(
            nome="Unidade do Profissional",
            endereco="Rua Secundária, 20",
        )
        cls.unidade_inativa = UnidadeSaude.objects.create(
            nome="Unidade Inativa",
            endereco="Rua Sem Uso, 30",
            ativo=False,
        )
        cls.profissional = Profissional.objects.create(
            nome="Profissional Ativa",
            cpf="98765432101",
            password="hash-de-teste",
            cargo="Médica",
            unidade=cls.outra_unidade,
        )
        cls.profissional_inativo = Profissional.objects.create(
            nome="Profissional Inativo",
            cpf="98765432102",
            password="hash-de-teste",
            cargo="Médico",
            unidade=cls.unidade,
            is_active=False,
        )
        cls.data_agendamento = timezone.make_aware(
            datetime(2026, 9, 10, 9, 0)
        )
        cls.data_exame = cls.data_agendamento + timedelta(days=1)

    def setUp(self):
        self.url = reverse("exames:criar")

    def dados_validos(self, **alteracoes):
        dados = {
            "usuario": self.cidadao.pk,
            "unidade": self.unidade.pk,
            "profissional": self.profissional.pk,
            "tipo": "Hemograma",
            "data_agendamento": self.data_agendamento.strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "data_exame": self.data_exame.strftime("%Y-%m-%dT%H:%M"),
        }
        dados.update(alteracoes)
        return dados

    def test_acesso_exige_autenticacao(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={self.url}",
        )

    def test_formulario_usa_card_com_largura_total(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        self.assertContains(
            resposta,
            'class="content-card content-card-wide"',
        )
        self.assertContains(
            resposta,
            'class="form-actions form-actions-centered"',
        )
        self.assertContains(resposta, reverse("usuarios_lista:lista"))
        self.assertContains(resposta, "Cancelar")

    def test_acesso_exige_servidor_com_as_duas_permissoes(self):
        for usuario in (
            self.cidadao,
            self.profissional,
            self.servidor_sem_permissao,
        ):
            with self.subTest(tipo=usuario.tipo):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_formulario_exibe_apenas_registros_ativos(self):
        formulario = CriacaoAgendamentoExameForm()

        self.assertQuerySetEqual(
            formulario.fields["usuario"].queryset,
            [self.cidadao],
        )
        self.assertNotIn(
            self.unidade_inativa,
            formulario.fields["unidade"].queryset,
        )
        self.assertNotIn(
            self.profissional_inativo,
            formulario.fields["profissional"].queryset,
        )

    def test_servidor_cria_agendamento_e_exame_atomicamente(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(self.url, self.dados_validos(), follow=True)

        self.assertRedirects(resposta, self.url)
        self.assertContains(resposta, "Agendamento e exame criados com sucesso")
        agendamento = Agendamento.objects.get()
        exame = Exame.objects.get()
        self.assertEqual(exame.agendamento, agendamento)
        self.assertEqual(exame.usuario, self.cidadao)
        self.assertEqual(exame.unidade, self.unidade)
        self.assertEqual(exame.profissional, self.profissional)
        self.assertEqual(exame.status, Exame.Status.CONFIRMADO)
        self.assertEqual(exame.resultado, "")
        notificacao = Notificacao.objects.get(
            exame=exame,
            tipo=Notificacao.TipoEvento.ATRIBUICAO,
        )
        self.assertEqual(notificacao.usuario_id, self.profissional.pk)
        self.assertFalse(notificacao.lida)
        self.assertIn(exame.tipo, notificacao.mensagem)

    def test_permite_profissional_de_unidade_diferente(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(self.url, self.dados_validos())

        self.assertEqual(resposta.status_code, 302)
        self.assertNotEqual(
            Exame.objects.get().unidade,
            Exame.objects.get().profissional.unidade,
        )

    def test_falha_no_exame_desfaz_criacao_do_agendamento(self):
        with patch(
            "exames.services.Exame.objects.create",
            side_effect=RuntimeError("falha simulada"),
        ):
            with self.assertRaisesMessage(RuntimeError, "falha simulada"):
                criar_agendamento_exame(
                    usuario=self.cidadao,
                    unidade=self.unidade,
                    profissional=self.profissional,
                    tipo="Hemograma",
                    data_agendamento=self.data_agendamento,
                    data_exame=self.data_exame,
                )

        self.assertFalse(Agendamento.objects.exists())

    def test_exige_data_do_exame_posterior_ao_agendamento(self):
        self.client.force_login(self.servidor)
        dados = self.dados_validos(
            data_exame=self.data_agendamento.strftime("%Y-%m-%dT%H:%M")
        )

        resposta = self.client.post(self.url, dados)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "deve ser posterior")
        self.assertFalse(Agendamento.objects.exists())
        self.assertFalse(Exame.objects.exists())

    def test_rejeita_registros_inativos_manipulados_no_post(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            self.dados_validos(
                usuario=self.cidadao_inativo.pk,
                unidade=self.unidade_inativa.pk,
                profissional=self.profissional_inativo.pk,
            ),
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Agendamento.objects.exists())
        self.assertFalse(Exame.objects.exists())

    def test_cabecalho_exibe_link_somente_ao_servidor_autorizado(self):
        self.client.force_login(self.servidor)
        resposta_autorizada = self.client.get(self.url)
        self.client.force_login(self.servidor_sem_permissao)
        resposta_negada = self.client.get(reverse("usuarios:inicio"))

        self.assertContains(resposta_autorizada, "Novo exame")
        self.assertNotContains(resposta_negada, "Novo exame")
