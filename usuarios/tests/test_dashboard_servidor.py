from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission

from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


class DashboardServidorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.servidor = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Servidor",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.servidor.user_permissions.add(
            *Permission.objects.filter(
                codename__in=("add_agendamento", "add_exame")
            )
        )
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadão ativo",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        Usuario.objects.create_user(
            cpf="12345678909",
            nome="Cidadão inativo",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
            is_active=False,
        )
        unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua Central, 100",
        )
        Profissional.objects.create(
            cpf="93541134780",
            nome="Profissional ativa",
            cargo="Médica",
            unidade=unidade,
        )
        Profissional.objects.create(
            cpf="39053344705",
            nome="Profissional inativo",
            cargo="Médico",
            unidade=unidade,
            is_active=False,
        )

    def setUp(self):
        self.url = reverse("usuarios:dashboard_servidor")

    def test_dashboard_exige_servidor_autenticado(self):
        self.assertRedirects(
            self.client.get(self.url),
            f"{reverse('usuarios:login')}?next={self.url}",
        )
        self.client.force_login(self.cidadao)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_dashboard_exibe_totais_por_perfil_e_situacao(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.context["totais"],
            {
                "cidadaos_ativos": 1,
                "cidadaos_inativos": 1,
                "profissionais_ativos": 1,
                "profissionais_inativos": 1,
            },
        )
        self.assertContains(resposta, 'class="stat-card"', count=4)

    def test_cards_apontam_para_listagens_filtradas(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        for parametros in (
            "tipo=CIDADAO&amp;situacao=ativo",
            "tipo=CIDADAO&amp;situacao=inativo",
            "tipo=PROFISSIONAL&amp;situacao=ativo",
            "tipo=PROFISSIONAL&amp;situacao=inativo",
        ):
            self.assertContains(resposta, parametros)

    def test_navegacao_do_servidor_respeita_ordem_definida(self):
        self.client.force_login(self.servidor)

        conteudo = self.client.get(self.url).content.decode()
        itens = (
            f'href="{reverse("usuarios:inicio")}">Minha conta',
            f'href="{self.url}">Dashboard',
            f'href="{reverse("usuarios_lista:lista")}">Usuários',
            f'href="{reverse("exames:criar")}">Novo exame',
        )

        posicoes = [conteudo.index(item) for item in itens]
        self.assertEqual(posicoes, sorted(posicoes))
