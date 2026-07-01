from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario


class LayoutCompartilhadoTests(TestCase):
    def test_pagina_publica_usa_layout_compartilhado(self):
        resposta = self.client.get(reverse("usuarios:login"))

        self.assertContains(resposta, "ExameSUS")
        self.assertContains(resposta, "Ir para o conteúdo principal")
        self.assertContains(resposta, "projeto acadêmico para gestão de exames")
        self.assertContains(resposta, "css/tokens.css")
        self.assertContains(resposta, "css/components.css")

    def test_cabecalho_autenticado_exibe_nome_e_sino(self):
        usuario = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        self.client.force_login(usuario)

        resposta = self.client.get(reverse("usuarios:inicio"))

        self.assertContains(resposta, usuario.nome)
        self.assertContains(resposta, "Nenhuma notificação pendente")
        self.assertContains(resposta, "Navegação estrutural")

    def test_cabecalho_anonimo_exibe_acoes_de_entrada_e_cadastro(self):
        resposta = self.client.get(reverse("usuarios:login"))

        self.assertContains(resposta, reverse("usuarios:login"))
        self.assertContains(resposta, reverse("usuarios:cadastro"))
