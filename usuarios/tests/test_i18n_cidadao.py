from datetime import datetime, timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


class InternacionalizacaoCidadaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
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
        cls.profissional.user_permissions.add(
            *Permission.objects.filter(
                codename__in=("view_exame", "change_exame")
            )
        )
        data = timezone.make_aware(datetime(2026, 10, 10, 14, 0))
        agendamento = Agendamento.objects.create(
            usuario=cls.cidadao,
            unidade=cls.unidade,
            data=data - timedelta(days=1),
        )
        cls.exame = Exame.objects.create(
            tipo="Hemograma",
            data=data,
            status=Exame.Status.CONFIRMADO,
            usuario=cls.cidadao,
            unidade=cls.unidade,
            profissional=cls.profissional,
            agendamento=agendamento,
        )

    def test_cidadao_visualiza_controle_de_idioma_ao_lado_do_sino(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(reverse("exames:lista"))

        self.assertContains(resposta, 'class="notification-bell"')
        self.assertContains(resposta, 'class="language-switcher"')
        self.assertContains(resposta, "Alterar idioma")

    def test_visitante_alterna_login_para_ingles(self):
        url = reverse("usuarios:login")

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, 'class="language-switcher"')
        self.assertContains(resposta, "Sign in to ExameSUS")
        self.assertContains(resposta, "Invalid CPF or password.", count=0)
        self.assertContains(resposta, "Do not have an account yet?")
        self.assertContains(resposta, "Create one")

    def test_cabecalho_usa_simbolo_de_saude_em_svg(self):
        resposta = self.client.get(reverse("usuarios:login"))

        self.assertContains(resposta, 'class="brand-mark"')
        self.assertContains(resposta, 'viewBox="0 0 32 32"')

    def test_alternancia_para_ingles_traduz_listagem_de_exames(self):
        self.client.force_login(self.cidadao)
        url = reverse("exames:lista")

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, '<html lang="en">')
        self.assertContains(resposta, "My exams")
        self.assertContains(resposta, "Filter exams")
        self.assertContains(resposta, "Apply filters")
        self.assertContains(resposta, "Confirmed")
        self.assertContains(resposta, "Sign out")

    def test_cidadao_pode_retornar_ao_portugues(self):
        self.client.force_login(self.cidadao)
        url = reverse("exames:lista")
        self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
        )

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "pt-br", "next": url},
            follow=True,
        )

        self.assertContains(resposta, '<html lang="pt-br">')
        self.assertContains(resposta, "Meus exames")

    def test_servidor_visualiza_controle_e_listagem_em_ingles(self):
        self.client.force_login(self.servidor)
        url = reverse("usuarios_lista:lista")

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, 'class="language-switcher"')
        self.assertContains(resposta, "Users")
        self.assertContains(resposta, "Filter users")
        self.assertContains(resposta, "New user")
        self.assertContains(resposta, "Deactivate selected")

    def test_tela_de_criacao_de_usuario_e_traduzida(self):
        self.client.force_login(self.servidor)
        url = reverse("usuarios_lista:criar")

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, "New user")
        self.assertContains(resposta, "Create user")
        self.assertContains(resposta, "Profile")

    def test_tela_de_edicao_de_profissional_e_traduzida(self):
        self.client.force_login(self.servidor)
        url = reverse(
            "usuarios_lista:editar_profissional",
            args=[self.profissional.pk],
        )

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, "Edit healthcare professional")
        self.assertContains(resposta, "Save changes")
        self.assertContains(resposta, "Specialty")

    def test_tela_de_criacao_de_exame_e_traduzida(self):
        self.client.force_login(self.servidor)
        url = reverse("exames:criar")

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, "Create appointment and exam")
        self.assertContains(resposta, "Exam type")
        self.assertContains(resposta, "Appointment date and time")

    def test_profissional_visualiza_controle_e_listagem_em_ingles(self):
        self.client.force_login(self.profissional)
        url = reverse("exames:lista_profissional")

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, 'class="language-switcher"')
        self.assertContains(resposta, "Assigned exams")
        self.assertContains(resposta, "View details")
        self.assertContains(resposta, "Delete exam")

    def test_detalhes_do_profissional_sao_traduzidos_para_ingles(self):
        self.client.force_login(self.profissional)
        url = reverse(
            "exames:detalhe_profissional",
            args=[self.exame.pk],
        )

        resposta = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": url},
            follow=True,
        )

        self.assertContains(resposta, "Exam details")
        self.assertContains(resposta, "Update exam status")
        self.assertContains(resposta, "Next status")
