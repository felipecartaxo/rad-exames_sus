from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from exames.services import transicionar_status
from notificacoes.models import Notificacao
from notificacoes.services import (
    criar_notificacao_exame_atribuido,
    criar_notificacao_resultado_disponivel,
)
from rede_saude.models import Profissional, UnidadeSaude


Usuario = get_user_model()


class NotificacaoTestMixin:
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
        cls.data = timezone.make_aware(datetime(2026, 8, 10, 14, 30))

    def criar_exame(
        self,
        usuario=None,
        status=Exame.Status.EM_ANALISE,
        tipo="Hemograma",
    ):
        usuario = usuario or self.cidadao
        agendamento = Agendamento.objects.create(
            usuario=usuario,
            unidade=self.unidade,
            data=self.data,
        )
        return Exame.objects.create(
            tipo=tipo,
            data=self.data,
            status=status,
            usuario=usuario,
            unidade=self.unidade,
            profissional=self.profissional,
            agendamento=agendamento,
        )


class NotificacaoServiceTests(NotificacaoTestMixin, TestCase):
    def test_atribuicao_cria_notificacao_para_profissional(self):
        exame = self.criar_exame()

        notificacao = criar_notificacao_exame_atribuido(exame)

        self.assertEqual(notificacao.usuario_id, self.profissional.pk)
        self.assertEqual(
            notificacao.tipo,
            Notificacao.TipoEvento.ATRIBUICAO,
        )
        self.assertFalse(notificacao.lida)
        self.assertIn(exame.tipo, notificacao.mensagem)

    def test_atribuicao_e_resultado_coexistem_no_mesmo_exame(self):
        exame = self.criar_exame(status=Exame.Status.RESULTADO_DISPONIVEL)

        atribuicao = criar_notificacao_exame_atribuido(exame)
        resultado = criar_notificacao_resultado_disponivel(exame)

        self.assertNotEqual(atribuicao, resultado)
        self.assertEqual(Notificacao.objects.filter(exame=exame).count(), 2)

    def test_transicao_para_resultado_disponivel_cria_notificacao(self):
        exame = self.criar_exame()

        transicionar_status(
            exame,
            Exame.Status.RESULTADO_DISPONIVEL,
            resultado="Resultado disponível para acompanhamento.",
        )

        notificacao = Notificacao.objects.get(exame=exame)
        self.assertEqual(notificacao.usuario, self.cidadao)
        self.assertFalse(notificacao.lida)
        self.assertIn(exame.tipo, notificacao.mensagem)

    def test_servico_cria_uma_unica_notificacao_por_exame(self):
        exame = self.criar_exame(status=Exame.Status.RESULTADO_DISPONIVEL)

        primeira = criar_notificacao_resultado_disponivel(exame)
        segunda = criar_notificacao_resultado_disponivel(exame)

        self.assertEqual(primeira, segunda)
        self.assertEqual(Notificacao.objects.filter(exame=exame).count(), 1)

    def test_servico_rejeita_exame_sem_resultado_disponivel(self):
        exame = self.criar_exame(status=Exame.Status.EM_ANALISE)

        with self.assertRaises(ValidationError):
            criar_notificacao_resultado_disponivel(exame)


class NotificacaoViewTests(NotificacaoTestMixin, TestCase):
    def setUp(self):
        self.url = reverse("notificacoes:lista")

    def criar_notificacao(self, usuario=None, lida=False, tipo="Hemograma"):
        exame = self.criar_exame(
            usuario=usuario,
            status=Exame.Status.RESULTADO_DISPONIVEL,
            tipo=tipo,
        )
        notificacao = criar_notificacao_resultado_disponivel(exame)
        if lida:
            notificacao.lida = True
            notificacao.save(update_fields=["lida"])
        return notificacao

    def test_pagina_exige_autenticacao(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={self.url}",
        )

    def test_servidor_recebe_acesso_negado(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 403)

    def test_profissional_visualiza_notificacao_de_atribuicao(self):
        exame = self.criar_exame()
        propria = criar_notificacao_exame_atribuido(exame)
        self.criar_notificacao()
        self.client.force_login(self.profissional)

        resposta = self.client.get(self.url)

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, propria.mensagem)
        self.assertContains(resposta, "1 notificação pendente")
        self.assertQuerySetEqual(resposta.context["notificacoes"], [propria])

    def test_profissional_marca_somente_as_proprias_como_lidas(self):
        exame = self.criar_exame()
        propria = criar_notificacao_exame_atribuido(exame)
        terceira = self.criar_notificacao()
        self.client.force_login(self.profissional)

        resposta = self.client.post(reverse("notificacoes:marcar_lidas"))
        propria.refresh_from_db()
        terceira.refresh_from_db()

        self.assertRedirects(resposta, self.url)
        self.assertTrue(propria.lida)
        self.assertFalse(terceira.lida)

    def test_cidadao_visualiza_somente_as_proprias_notificacoes(self):
        propria = self.criar_notificacao()
        terceira = self.criar_notificacao(
            usuario=self.outro_cidadao,
            tipo="Radiografia",
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, propria.mensagem)
        self.assertNotContains(resposta, terceira.mensagem)
        self.assertQuerySetEqual(resposta.context["notificacoes"], [propria])

    def test_badge_exibe_quantidade_de_notificacoes_nao_lidas(self):
        self.criar_notificacao()
        self.criar_notificacao()
        self.criar_notificacao(lida=True)
        self.client.force_login(self.cidadao)

        resposta = self.client.get(reverse("exames:lista"))

        self.assertContains(resposta, "2 notificações pendentes")
        self.assertContains(resposta, 'class="notification-count"')

    def test_badge_fica_oculta_quando_nao_ha_pendencias(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(reverse("exames:lista"))

        self.assertContains(resposta, "Nenhuma notificação pendente")
        self.assertNotContains(resposta, 'class="notification-count"')

    def test_marcar_como_lidas_atualiza_apenas_notificacoes_do_cidadao(self):
        propria = self.criar_notificacao()
        terceira = self.criar_notificacao(usuario=self.outro_cidadao)
        self.client.force_login(self.cidadao)

        resposta = self.client.post(reverse("notificacoes:marcar_lidas"))
        propria.refresh_from_db()
        terceira.refresh_from_db()

        self.assertRedirects(resposta, self.url)
        self.assertTrue(propria.lida)
        self.assertFalse(terceira.lida)
