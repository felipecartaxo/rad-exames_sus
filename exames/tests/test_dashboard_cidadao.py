from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


class DashboardCidadaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadão",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.outro_cidadao = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Outro cidadão",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.servidor = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Servidor",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua Central, 100",
        )
        cls.profissional = Profissional.objects.create(
            cpf="93541134780",
            nome="Profissional",
            cargo="Médica",
            unidade=cls.unidade,
        )
        cls.data = timezone.make_aware(datetime(2026, 10, 10, 14, 0))
        for indice, status in enumerate(Exame.Status.values):
            cls.criar_exame(cls.cidadao, status, indice)
        cls.criar_exame(cls.outro_cidadao, Exame.Status.CONFIRMADO, 5)

    @classmethod
    def criar_exame(cls, cidadao, status, indice):
        agendamento = Agendamento.objects.create(
            usuario=cidadao,
            unidade=cls.unidade,
            data=cls.data + timedelta(hours=indice),
        )
        return Exame.objects.create(
            tipo=f"Exame {indice}",
            data=agendamento.data + timedelta(hours=1),
            status=status,
            resultado=(
                "Resultado"
                if status == Exame.Status.RESULTADO_DISPONIVEL
                else ""
            ),
            usuario=cidadao,
            unidade=cls.unidade,
            profissional=cls.profissional,
            agendamento=agendamento,
        )

    def setUp(self):
        self.url = reverse("exames:dashboard_cidadao")

    def test_dashboard_exige_cidadao_autenticado(self):
        self.assertRedirects(
            self.client.get(self.url),
            f"{reverse('usuarios:login')}?next={self.url}",
        )
        self.client.force_login(self.servidor)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_dashboard_contabiliza_somente_exames_do_cidadao(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertEqual(
            resposta.context["totais"],
            {
                "confirmados": 1,
                "em_analise": 1,
                "resultados_disponiveis": 1,
                "cancelados": 1,
            },
        )
        self.assertContains(resposta, 'class="stat-card"', count=4)

    def test_cabecalho_exibe_dashboard_apos_minha_conta(self):
        self.client.force_login(self.cidadao)

        conteudo = self.client.get(self.url).content.decode()

        minha_conta = conteudo.index(
            f'href="{reverse("usuarios:inicio")}">Minha conta'
        )
        dashboard = conteudo.index(f'href="{self.url}">Dashboard')
        self.assertLess(minha_conta, dashboard)

    def test_cards_finais_abrem_historico_com_status_filtrado(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        historico = reverse("exames:historico")
        self.assertContains(
            resposta,
            f"{historico}?status=RESULTADO_DISPONIVEL",
        )
        self.assertContains(
            resposta,
            f"{historico}?status=CANCELADO",
        )
