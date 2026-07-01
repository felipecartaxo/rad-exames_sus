from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from rede_saude.models import Profissional, UnidadeSaude


Usuario = get_user_model()


class ExameHistoricoViewTests(TestCase):
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
        self.url = reverse("exames:historico")

    def criar_exame(self, usuario=None, agendamento=None, **alteracoes):
        usuario = usuario or self.cidadao
        agendamento = agendamento or self.agendamento
        dados = {
            "tipo": "Hemograma",
            "data": self.data_base,
            "status": Exame.Status.RESULTADO_DISPONIVEL,
            "resultado": "Valores dentro da referência informada.",
            "usuario": usuario,
            "unidade": self.unidade,
            "profissional": self.profissional,
            "agendamento": agendamento,
        }
        dados.update(alteracoes)
        return Exame.objects.create(**dados)

    def test_historico_exige_autenticacao(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={self.url}",
        )

    def test_servidor_recebe_acesso_negado(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 403)

    def test_historico_nao_expoe_exame_de_outro_cidadao(self):
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

    def test_historico_apresenta_todos_os_dados_e_resultado(self):
        exame = self.criar_exame()
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, exame.tipo)
        self.assertContains(resposta, exame.get_status_display())
        self.assertContains(resposta, self.unidade.nome)
        self.assertContains(resposta, self.profissional.nome)
        self.assertContains(resposta, exame.resultado)

    def test_historico_exibe_mensagem_quando_resultado_nao_existe(self):
        self.criar_exame(
            status=Exame.Status.EM_ANALISE,
            resultado="",
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Resultado ainda não disponível.")

    def test_historico_exibe_estado_vazio(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Histórico vazio")

    def test_historico_ordena_por_data_e_id_decrescentes(self):
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

    def test_historico_possui_cinco_exames_por_pagina(self):
        for indice in range(7):
            self.criar_exame(
                tipo=f"Exame {indice:02d}",
                data=self.data_base + timedelta(minutes=indice),
            )
        self.client.force_login(self.cidadao)

        primeira = self.client.get(self.url)
        segunda = self.client.get(self.url, {"page": 2})

        self.assertEqual(len(primeira.context["exames"]), 5)
        self.assertEqual(len(segunda.context["exames"]), 2)

