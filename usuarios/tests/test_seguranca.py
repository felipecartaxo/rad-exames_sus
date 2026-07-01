from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from usuarios.models import Usuario


class SegurancaFuncionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.servidor = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Servidor Autorizado",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        permissao = Permission.objects.get(
            content_type__app_label="usuarios",
            codename="view_usuario",
        )
        cls.servidor.user_permissions.add(permissao)
        cls.superusuario = Usuario.objects.create_superuser(
            cpf="12345678909",
            nome="Administrador de Teste",
            password="senha-segura-123",
        )

    def test_usuario_desativado_perde_acesso_as_paginas_privadas(self):
        self.client.force_login(self.cidadao)
        self.cidadao.is_active = False
        self.cidadao.save(update_fields=["is_active"])

        for url in (
            reverse("usuarios:inicio"),
            reverse("exames:lista"),
            reverse("exames:historico"),
            reverse("notificacoes:lista"),
        ):
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertEqual(resposta.status_code, 302)
                self.assertTrue(resposta.url.startswith(reverse("usuarios:login")))

    def test_superusuario_pode_acessar_lista_de_usuarios(self):
        self.client.force_login(self.superusuario)

        resposta = self.client.get(reverse("usuarios_lista:lista"))

        self.assertEqual(resposta.status_code, 200)

    def test_resposta_403_apresenta_mensagem_compreensivel(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(reverse("usuarios_lista:lista"))

        self.assertEqual(resposta.status_code, 403)
        self.assertContains(
            resposta,
            "Você não tem permissão para acessar esta página.",
            status_code=403,
        )

    def test_navegacao_do_cidadao_nao_exibe_link_de_usuarios(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(reverse("exames:lista"))

        self.assertNotContains(resposta, 'href="/usuarios/"')

    def test_navegacao_do_servidor_nao_exibe_links_do_cidadao(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(reverse("usuarios_lista:lista"))

        self.assertNotContains(resposta, 'href="/exames/"')
        self.assertNotContains(resposta, 'href="/exames/historico/"')
        self.assertNotContains(resposta, 'href="/notificacoes/"')

    def test_logout_rejeita_post_sem_token_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.cidadao)

        resposta = cliente.post(reverse("usuarios:logout"))

        self.assertEqual(resposta.status_code, 403)

    def test_marcacao_de_notificacoes_rejeita_post_sem_token_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.cidadao)

        resposta = cliente.post(reverse("notificacoes:marcar_lidas"))

        self.assertEqual(resposta.status_code, 403)

    def test_servidor_nao_pode_marcar_notificacoes_como_lidas(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(reverse("notificacoes:marcar_lidas"))

        self.assertEqual(resposta.status_code, 403)

    def test_servidor_comum_nao_acessa_django_admin(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(reverse("admin:index"))

        self.assertEqual(resposta.status_code, 302)

