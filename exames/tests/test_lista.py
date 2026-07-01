from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from rede_saude.models import Profissional, UnidadeSaude


Usuario = get_user_model()


class ExameListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.outro_cidadao = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Outra Cidadã",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.servidor = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Servidor de Teste",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua das Flores, 100",
        )
        cls.profissional = Profissional.objects.create(
            nome="Profissional de Teste",
            cpf="98765432100",
            cargo="Médica",
            unidade=cls.unidade,
        )
        cls.data_base = timezone.make_aware(datetime(2026, 8, 10, 14, 30))
        cls.agendamento = Agendamento.objects.create(
            usuario=cls.cidadao,
            unidade=cls.unidade,
            data=cls.data_base,
        )
        cls.outro_agendamento = Agendamento.objects.create(
            usuario=cls.outro_cidadao,
            unidade=cls.unidade,
            data=cls.data_base,
        )

    def setUp(self):
        self.url = reverse("exames:lista")

    def criar_exame(self, usuario=None, agendamento=None, **alteracoes):
        usuario = usuario or self.cidadao
        agendamento = agendamento or self.agendamento
        dados = {
            "tipo": "Hemograma",
            "data": self.data_base,
            "status": Exame.Status.AGENDADO,
            "usuario": usuario,
            "unidade": self.unidade,
            "profissional": self.profissional,
            "agendamento": agendamento,
        }
        dados.update(alteracoes)
        return Exame.objects.create(**dados)

    def test_usuario_anonimo_e_direcionado_ao_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={self.url}",
        )

    def test_servidor_recebe_acesso_negado(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 403)

    def test_cidadao_visualiza_somente_os_proprios_exames(self):
        proprio = self.criar_exame(tipo="Exame próprio")
        terceiro = self.criar_exame(
            usuario=self.outro_cidadao,
            agendamento=self.outro_agendamento,
            tipo="Exame de terceiro",
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, proprio.tipo)
        self.assertNotContains(resposta, terceiro.tipo)
        self.assertQuerySetEqual(resposta.context["exames"], [proprio])

    def test_lista_apresenta_dados_essenciais(self):
        exame = self.criar_exame(status=Exame.Status.CONFIRMADO)
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, exame.tipo)
        self.assertContains(resposta, exame.get_status_display())
        self.assertContains(resposta, self.unidade.nome)
        self.assertContains(resposta, "Data e horário")

    def test_lista_exibe_estado_vazio(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Nenhum exame encontrado")

    def test_ordenacao_usa_data_e_id_decrescentes(self):
        antigo = self.criar_exame(
            tipo="Antigo",
            data=self.data_base - timedelta(days=1),
        )
        recente = self.criar_exame(
            tipo="Recente",
            data=self.data_base + timedelta(days=1),
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertQuerySetEqual(
            resposta.context["exames"],
            [recente, antigo],
        )

    def test_lista_possui_dez_exames_por_pagina(self):
        for indice in range(12):
            self.criar_exame(
                tipo=f"Exame {indice:02d}",
                data=self.data_base + timedelta(minutes=indice),
            )
        self.client.force_login(self.cidadao)

        primeira = self.client.get(self.url)
        segunda = self.client.get(self.url, {"page": 2})

        self.assertEqual(len(primeira.context["exames"]), 10)
        self.assertTrue(primeira.context["page_obj"].has_next())
        self.assertEqual(len(segunda.context["exames"]), 2)

    def test_login_de_cidadao_redireciona_para_exames(self):
        resposta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.cidadao.cpf,
                "password": "senha-segura-123",
            },
        )

        self.assertRedirects(resposta, self.url)

