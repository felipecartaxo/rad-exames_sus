from django.test import TestCase
from django.urls import reverse

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

    def test_cidadao_visualiza_controle_de_idioma_ao_lado_do_sino(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(reverse("exames:lista"))

        self.assertContains(resposta, 'class="notification-bell"')
        self.assertContains(resposta, 'class="language-switcher"')
        self.assertContains(resposta, "Alterar idioma")

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
        self.assertContains(resposta, "No exams found")
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

    def test_servidor_ainda_nao_visualiza_controle_de_idioma(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(reverse("usuarios_lista:lista"))

        self.assertNotContains(resposta, 'class="language-switcher"')
