from django.test import TestCase
from django.urls import reverse

from usuarios.models import Usuario


class LayoutCompartilhadoTests(TestCase):
    def test_pagina_publica_usa_layout_compartilhado(self):
        resposta = self.client.get(reverse("usuarios:login"))

        self.assertContains(resposta, "ExameSUS")

    def test_rodape_destaca_plataforma_slogan_e_exibe_desenvolvedores(self):
        resposta = self.client.get(reverse("usuarios:login"))

        self.assertContains(
            resposta,
            "Cuidando da saúde e valorizando a vida de cada cidadão.",
        )
        self.assertContains(resposta, 'class="footer-brand"')
        self.assertContains(resposta, 'class="footer-slogan"')
        for nome in (
            "Felipe Cartaxo",
            "Leidiana Patrício",
            "Thiago Santos",
            "Sheila Lee",
        ):
            self.assertContains(resposta, nome)
        self.assertNotContains(resposta, "projeto acadêmico")
        self.assertNotContains(resposta, "RAD - Desenvolvimento Ágil")
        self.assertContains(resposta, "Ir para o conteúdo principal")
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
