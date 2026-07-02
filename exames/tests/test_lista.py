import tempfile
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from rede_saude.models import Profissional, UnidadeSaude


Usuario = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
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
            "status": Exame.Status.CONFIRMADO,
            "usuario": usuario,
            "unidade": agendamento.unidade,
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

    def test_lista_exibe_anexo_somente_quando_disponivel(self):
        com_anexo = self.criar_exame(
            tipo="Exame com anexo",
            status=Exame.Status.EM_ANALISE,
            documento_resultado=SimpleUploadedFile(
                "resultado.pdf",
                b"%PDF-1.4 documento de teste",
                content_type="application/pdf",
            ),
        )
        self.criar_exame(tipo="Exame sem anexo")
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Visualizar anexo do resultado", count=1)
        self.assertContains(
            resposta,
            reverse("exames:documento_resultado", args=[com_anexo.pk]),
        )
        self.assertContains(resposta, 'class="record-card-actions"')

    def test_lista_exibe_apenas_exames_em_andamento(self):
        confirmado = self.criar_exame(
            tipo="Confirmado",
            status=Exame.Status.CONFIRMADO,
        )
        em_analise = self.criar_exame(
            tipo="Em análise",
            status=Exame.Status.EM_ANALISE,
        )
        resultado = self.criar_exame(
            tipo="Finalizado",
            status=Exame.Status.RESULTADO_DISPONIVEL,
            resultado="Disponível",
        )
        cancelado = self.criar_exame(
            tipo="Cancelado",
            status=Exame.Status.CANCELADO,
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)

        self.assertQuerySetEqual(
            resposta.context["exames"],
            [em_analise, confirmado],
            ordered=False,
        )
        self.assertNotIn(resultado, resposta.context["exames"])
        self.assertNotIn(cancelado, resposta.context["exames"])

    def test_filtro_oferece_somente_status_em_andamento(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url)
        escolhas = dict(
            resposta.context["form_filtros"].fields["status"].choices
        )

        self.assertIn(Exame.Status.CONFIRMADO, escolhas)
        self.assertIn(Exame.Status.EM_ANALISE, escolhas)
        self.assertNotIn(Exame.Status.RESULTADO_DISPONIVEL, escolhas)
        self.assertNotIn(Exame.Status.CANCELADO, escolhas)

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

    def test_filtra_exames_por_status(self):
        self.criar_exame(tipo="Confirmado")
        em_analise = self.criar_exame(
            tipo="Em análise",
            status=Exame.Status.EM_ANALISE,
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(
            self.url,
            {"status": Exame.Status.EM_ANALISE},
        )

        self.assertQuerySetEqual(resposta.context["exames"], [em_analise])

    def test_filtra_por_faixa_inclusiva_de_data_e_horario(self):
        anterior = self.criar_exame(
            tipo="Anterior",
            data=self.data_base - timedelta(hours=2),
        )
        inicio = self.criar_exame(
            tipo="No início",
            data=self.data_base,
        )
        fim = self.criar_exame(
            tipo="No fim",
            data=self.data_base + timedelta(hours=1),
        )
        posterior = self.criar_exame(
            tipo="Posterior",
            data=self.data_base + timedelta(hours=2),
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(
            self.url,
            {
                "data_inicio": self.data_base.strftime("%Y-%m-%dT%H:%M"),
                "data_fim": (self.data_base + timedelta(hours=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
            },
        )

        self.assertQuerySetEqual(resposta.context["exames"], [fim, inicio])
        self.assertNotContains(resposta, anterior.tipo)
        self.assertNotContains(resposta, posterior.tipo)

    def test_filtra_por_unidade_sem_expor_unidade_de_terceiro(self):
        outra_unidade = UnidadeSaude.objects.create(
            nome="Unidade Norte",
            endereco="Avenida Norte, 200",
            ativo=False,
        )
        unidade_terceiro = UnidadeSaude.objects.create(
            nome="Unidade exclusiva de terceiro",
            endereco="Rua Privada, 30",
        )
        agendamento_norte = Agendamento.objects.create(
            usuario=self.cidadao,
            unidade=outra_unidade,
            data=self.data_base,
        )
        agendamento_terceiro = Agendamento.objects.create(
            usuario=self.outro_cidadao,
            unidade=unidade_terceiro,
            data=self.data_base,
        )
        central = self.criar_exame(tipo="Exame central")
        norte = self.criar_exame(
            tipo="Exame norte",
            agendamento=agendamento_norte,
        )
        self.criar_exame(
            tipo="Exame de terceiro",
            usuario=self.outro_cidadao,
            agendamento=agendamento_terceiro,
        )
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url, {"unidade": outra_unidade.pk})

        self.assertQuerySetEqual(resposta.context["exames"], [norte])
        self.assertNotContains(resposta, central.tipo)
        unidades = resposta.context["form_filtros"].fields["unidade"].queryset
        self.assertIn(outra_unidade, unidades)
        self.assertNotIn(unidade_terceiro, unidades)

    def test_faixa_invalida_exibe_erro_e_nao_filtra(self):
        exame = self.criar_exame()
        self.client.force_login(self.cidadao)

        resposta = self.client.get(
            self.url,
            {
                "data_inicio": self.data_base.strftime("%Y-%m-%dT%H:%M"),
                "data_fim": (self.data_base - timedelta(hours=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
            },
        )

        self.assertContains(resposta, "A data final deve ser")
        self.assertQuerySetEqual(resposta.context["exames"], [exame])

    def test_lista_possui_cinco_exames_por_pagina(self):
        for indice in range(12):
            self.criar_exame(
                tipo=f"Exame {indice:02d}",
                data=self.data_base + timedelta(minutes=indice),
            )
        self.client.force_login(self.cidadao)

        primeira = self.client.get(self.url)
        segunda = self.client.get(self.url, {"page": 2})
        terceira = self.client.get(self.url, {"page": 3})

        self.assertEqual(len(primeira.context["exames"]), 5)
        self.assertTrue(primeira.context["page_obj"].has_next())
        self.assertEqual(len(segunda.context["exames"]), 5)
        self.assertEqual(len(terceira.context["exames"]), 2)

    def test_login_de_cidadao_redireciona_para_exames(self):
        resposta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.cidadao.cpf,
                "password": "senha-segura-123",
            },
        )

        self.assertRedirects(resposta, self.url)
