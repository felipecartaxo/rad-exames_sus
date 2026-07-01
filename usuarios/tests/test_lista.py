from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario


class UsuarioListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.permissao = Permission.objects.get(
            content_type__app_label="usuarios",
            codename="view_usuario",
        )
        cls.servidor = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Servidor Autorizado",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.servidor.user_permissions.add(cls.permissao)
        cls.servidor_sem_permissao = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Servidor sem Permissão",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.cidadao = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )

    def setUp(self):
        self.url = reverse("usuarios_lista:lista")

    def test_usuario_anonimo_e_direcionado_ao_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={self.url}",
        )

    def test_cidadao_recebe_acesso_negado(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 403)

    def test_servidor_sem_permissao_recebe_acesso_negado(self):
        self.client.force_login(self.servidor_sem_permissao)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 403)

    def test_servidor_com_permissao_visualiza_lista(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, self.cidadao.nome)

    def test_listagem_possui_dez_registros_por_pagina(self):
        for indice in range(12):
            Usuario.objects.create_user(
                cpf=f"900000000{indice:02d}",
                nome=f"Pessoa {indice:02d}",
                tipo=Usuario.Tipo.CIDADAO,
                password="senha-segura-123",
            )
        self.client.force_login(self.servidor)

        primeira = self.client.get(self.url)
        segunda = self.client.get(self.url, {"page": 2})

        self.assertEqual(len(primeira.context["usuarios"]), 10)
        self.assertTrue(primeira.context["page_obj"].has_next())
        self.assertGreater(len(segunda.context["usuarios"]), 0)

    def test_ordenacao_e_estavel_por_nome_cpf_e_id(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)
        usuarios = list(resposta.context["usuarios"])
        esperado = sorted(
            usuarios,
            key=lambda usuario: (usuario.nome, usuario.cpf, usuario.pk),
        )

        self.assertEqual(usuarios, esperado)

    def test_login_de_servidor_autorizado_redireciona_para_lista(self):
        resposta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.servidor.cpf,
                "password": "senha-segura-123",
            },
        )

        self.assertRedirects(resposta, self.url)

