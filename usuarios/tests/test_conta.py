from django.contrib.auth import SESSION_KEY
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario


class ContaViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Usuária",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.outro_usuario = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Outro usuário",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )

    def setUp(self):
        self.url = reverse("usuarios:inicio")

    def test_pagina_exige_autenticacao(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={self.url}",
        )

    def test_pagina_exibe_dois_cards_de_largura_total(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(self.url)

        self.assertContains(
            resposta,
            'class="content-card content-card-wide account-card"',
            count=2,
        )
        self.assertContains(resposta, "Meus dados")
        self.assertContains(resposta, self.usuario.get_tipo_display())

    def test_formulario_nao_expoe_perfil_situacao_ou_permissoes(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(self.url)
        campos = resposta.context["form"].fields

        self.assertEqual(
            set(campos),
            {"nome", "cpf", "password1", "password2"},
        )

    def test_usuario_atualiza_nome_e_cpf_sem_alterar_senha(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            self.url,
            {
                "nome": "Nome atualizado",
                "cpf": "529.982.247-25",
                "password1": "",
                "password2": "",
            },
        )

        self.assertRedirects(resposta, self.url)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nome, "Nome atualizado")
        self.assertEqual(self.usuario.cpf, "52998224725")
        self.assertTrue(self.usuario.check_password("senha-segura-123"))

    def test_usuario_redefine_senha_sem_perder_sessao(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            self.url,
            {
                "nome": self.usuario.nome,
                "cpf": self.usuario.cpf,
                "password1": "nova-senha-segura-456",
                "password2": "nova-senha-segura-456",
            },
        )

        self.assertRedirects(resposta, self.url)
        self.usuario.refresh_from_db()
        self.assertTrue(
            self.usuario.check_password("nova-senha-segura-456")
        )
        self.assertEqual(
            int(self.client.session[SESSION_KEY]),
            self.usuario.pk,
        )

    def test_formulario_rejeita_cpf_de_outro_usuario(self):
        self.client.force_login(self.usuario)

        resposta = self.client.post(
            self.url,
            {
                "nome": self.usuario.nome,
                "cpf": self.outro_usuario.cpf,
                "password1": "",
                "password2": "",
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Já existe uma conta")
