from django.contrib.auth import SESSION_KEY
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario


class AutenticacaoTests(TestCase):
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
            nome="Servidor de Teste",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.superusuario = Usuario.objects.create_superuser(
            cpf="12345678909",
            nome="Administrador de Teste",
            password="senha-segura-123",
        )

    def setUp(self):
        self.login_url = reverse("usuarios:login")
        self.inicio_url = reverse("usuarios:inicio")

    def fazer_login(self, cpf="52998224725", senha="senha-segura-123"):
        return self.client.post(
            self.login_url,
            {"username": cpf, "password": senha},
        )

    def test_tela_de_login_exibe_campos_de_cpf_e_senha(self):
        resposta = self.client.get(self.login_url)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CPF")
        self.assertContains(resposta, 'type="password"')

    def test_acoes_do_login_possuem_alinhamento_e_espacamento_proprios(self):
        resposta = self.client.get(self.login_url)

        self.assertContains(resposta, 'class="form-actions login-actions"')
        self.assertContains(resposta, 'class="login-signup"')

    def test_login_valido_cria_sessao(self):
        resposta = self.fazer_login()

        self.assertRedirects(resposta, reverse("exames:lista"))
        self.assertEqual(
            int(self.client.session[SESSION_KEY]),
            self.cidadao.pk,
        )

    def test_login_aceita_cpf_formatado(self):
        resposta = self.fazer_login(cpf="529.982.247-25")

        self.assertRedirects(resposta, reverse("exames:lista"))
        self.assertIn(SESSION_KEY, self.client.session)

    def test_senha_invalida_exibe_erro_generico(self):
        resposta = self.fazer_login(senha="senha-incorreta")

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CPF ou senha inválidos.")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_cpf_inexistente_exibe_o_mesmo_erro_generico(self):
        resposta = self.fazer_login(cpf="98765432100")

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CPF ou senha inválidos.")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_usuario_inativo_nao_pode_entrar(self):
        self.cidadao.is_active = False
        self.cidadao.save(update_fields=["is_active"])

        resposta = self.fazer_login()

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "CPF ou senha inválidos.")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_servidor_comum_e_direcionado_para_lista_de_usuarios(self):
        resposta = self.fazer_login(cpf=self.servidor.cpf)

        self.assertRedirects(resposta, reverse("usuarios_lista:lista"))

    def test_superusuario_e_direcionado_para_admin(self):
        resposta = self.fazer_login(cpf=self.superusuario.cpf)

        self.assertRedirects(resposta, reverse("admin:index"))

    def test_redirecionamento_next_e_respeitado(self):
        resposta = self.client.post(
            f"{self.login_url}?next={self.inicio_url}",
            {
                "username": self.cidadao.cpf,
                "password": "senha-segura-123",
                "next": self.inicio_url,
            },
        )

        self.assertRedirects(resposta, self.inicio_url)

    def test_pagina_privada_redireciona_usuario_anonimo(self):
        resposta = self.client.get(self.inicio_url)

        self.assertRedirects(
            resposta,
            f"{self.login_url}?next={self.inicio_url}",
        )

    def test_logout_por_post_encerra_sessao(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.post(reverse("usuarios:logout"))

        self.assertRedirects(resposta, self.login_url)
        self.assertNotIn(SESSION_KEY, self.client.session)
