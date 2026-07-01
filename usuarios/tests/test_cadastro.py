from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from usuarios.forms import CadastroCidadaoForm


Usuario = get_user_model()


class CadastroCidadaoFormTests(TestCase):
    def dados_validos(self, **alteracoes):
        dados = {
            "nome": "Cidadã de Teste",
            "cpf": "529.982.247-25",
            "password1": "uma-senha-forte-123",
            "password2": "uma-senha-forte-123",
        }
        dados.update(alteracoes)
        return dados

    def test_formulario_cria_cidadao_com_cpf_normalizado_e_senha_protegida(self):
        formulario = CadastroCidadaoForm(data=self.dados_validos())

        self.assertTrue(formulario.is_valid(), formulario.errors)
        usuario = formulario.save()

        self.assertEqual(usuario.cpf, "52998224725")
        self.assertEqual(usuario.tipo, Usuario.Tipo.CIDADAO)
        self.assertTrue(usuario.check_password("uma-senha-forte-123"))
        self.assertFalse(usuario.is_staff)

    def test_formulario_rejeita_cpf_invalido(self):
        formulario = CadastroCidadaoForm(
            data=self.dados_validos(cpf="529.982.247-24")
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("cpf", formulario.errors)

    def test_formulario_rejeita_cpf_duplicado_mesmo_formatado(self):
        Usuario.objects.create_user(
            cpf="52998224725",
            nome="Conta Existente",
            tipo=Usuario.Tipo.CIDADAO,
            password="outra-senha-forte-123",
        )
        formulario = CadastroCidadaoForm(data=self.dados_validos())

        self.assertFalse(formulario.is_valid())
        self.assertIn("cpf", formulario.errors)

    def test_formulario_rejeita_confirmacao_de_senha_diferente(self):
        formulario = CadastroCidadaoForm(
            data=self.dados_validos(password2="senha-diferente-123")
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("password2", formulario.errors)

    def test_formulario_aplica_validadores_de_senha_configurados(self):
        formulario = CadastroCidadaoForm(
            data=self.dados_validos(password1="123", password2="123")
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("password2", formulario.errors)


class CadastroCidadaoViewTests(TestCase):
    def setUp(self):
        self.url = reverse("usuarios:cadastro")

    def test_pagina_de_cadastro_e_publica(self):
        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Crie sua conta")

    def test_cadastro_valido_persiste_usuario_e_exibe_sucesso(self):
        resposta = self.client.post(
            self.url,
            {
                "nome": "Cidadã de Teste",
                "cpf": "529.982.247-25",
                "password1": "uma-senha-forte-123",
                "password2": "uma-senha-forte-123",
            },
            follow=True,
        )

        self.assertRedirects(resposta, self.url)
        self.assertContains(resposta, "Cadastro realizado com sucesso.")
        usuario = Usuario.objects.get(cpf="52998224725")
        self.assertEqual(usuario.tipo, Usuario.Tipo.CIDADAO)

    def test_tipo_nao_e_exposto_no_formulario(self):
        resposta = self.client.get(self.url)

        self.assertNotContains(resposta, 'name="tipo"')

