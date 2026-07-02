from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario


class EdicaoUsuarioServidorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.servidor = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Servidor",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.cidadao = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Cidadão original",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.superusuario = Usuario.objects.create_superuser(
            cpf="11144477735",
            nome="Administrador",
            password="senha-segura-123",
        )
        cls.profissional = Usuario.objects.create_user(
            cpf="93541134780",
            nome="Profissional",
            tipo=Usuario.Tipo.PROFISSIONAL,
            password="senha-segura-123",
        )

    def setUp(self):
        self.url = reverse("usuarios_lista:editar", args=[self.cidadao.pk])

    def test_acesso_exige_perfil_servidor(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.cidadao)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_login(self.servidor)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_servidor_edita_dados_sem_alterar_senha(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            {
                "nome": "Cidadão atualizado",
                "cpf": "123.456.789-09",
                "tipo": Usuario.Tipo.SERVIDOR,
                "password1": "",
                "password2": "",
            },
        )

        self.assertRedirects(resposta, reverse("usuarios_lista:lista"))
        self.cidadao.refresh_from_db()
        self.assertEqual(self.cidadao.nome, "Cidadão atualizado")
        self.assertEqual(self.cidadao.cpf, "12345678909")
        self.assertEqual(self.cidadao.tipo, Usuario.Tipo.SERVIDOR)
        self.assertTrue(self.cidadao.check_password("senha-segura-123"))

    def test_servidor_pode_redefinir_senha(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            {
                "nome": self.cidadao.nome,
                "cpf": self.cidadao.cpf,
                "tipo": self.cidadao.tipo,
                "password1": "nova-senha-segura-456",
                "password2": "nova-senha-segura-456",
            },
        )

        self.assertRedirects(resposta, reverse("usuarios_lista:lista"))
        self.cidadao.refresh_from_db()
        self.assertTrue(self.cidadao.check_password("nova-senha-segura-456"))

    def test_nao_permite_editar_profissional_ou_superusuario(self):
        self.client.force_login(self.servidor)

        for usuario in (self.profissional, self.superusuario):
            url = reverse("usuarios_lista:editar", args=[usuario.pk])
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_rejeita_cpf_de_outro_usuario(self):
        outro = Usuario.objects.create_user(
            cpf="39053344705",
            nome="Outro cidadão",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            {
                "nome": self.cidadao.nome,
                "cpf": outro.cpf,
                "tipo": self.cidadao.tipo,
                "password1": "",
                "password2": "",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Já existe uma conta")
