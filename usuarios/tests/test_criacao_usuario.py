from django.test import TestCase
from django.urls import reverse

from usuarios.forms import CriacaoUsuarioServidorForm
from usuarios.models import Usuario


class CriacaoUsuarioServidorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.servidor = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Servidor autorizado",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.servidor_sem_permissao = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Servidor sem permissão",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.cidadao = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Cidadão",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )

    def setUp(self):
        self.url = reverse("usuarios_lista:criar")

    def test_formulario_nao_oferece_perfil_profissional(self):
        valores = dict(CriacaoUsuarioServidorForm().fields["tipo"].choices)

        self.assertIn(Usuario.Tipo.CIDADAO, valores)
        self.assertIn(Usuario.Tipo.SERVIDOR, valores)
        self.assertNotIn(Usuario.Tipo.PROFISSIONAL, valores)

    def test_acesso_exige_apenas_perfil_servidor(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.cidadao)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_login(self.servidor_sem_permissao)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_servidor_cria_usuario_com_senha_protegida(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            {
                "nome": "Nova Servidora",
                "cpf": "935.411.347-80",
                "tipo": Usuario.Tipo.SERVIDOR,
                "password1": "senha-segura-456",
                "password2": "senha-segura-456",
            },
        )

        self.assertRedirects(resposta, reverse("usuarios_lista:lista"))
        usuario = Usuario.objects.get(cpf="93541134780")
        self.assertEqual(usuario.tipo, Usuario.Tipo.SERVIDOR)
        self.assertTrue(usuario.check_password("senha-segura-456"))

    def test_formulario_rejeita_cpf_duplicado(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            {
                "nome": "Duplicado",
                "cpf": "123.456.789-09",
                "tipo": Usuario.Tipo.CIDADAO,
                "password1": "senha-segura-456",
                "password2": "senha-segura-456",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Já existe uma conta")
        self.assertEqual(Usuario.objects.filter(cpf="12345678909").count(), 1)
