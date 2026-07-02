import tempfile
from datetime import datetime, timedelta

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from notificacoes.models import Notificacao
from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ExameProfissionalDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.outro_cidadao = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Outra Cidadã",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua Principal, 10",
        )
        permissoes = Permission.objects.filter(
            codename__in=("view_exame", "change_exame")
        )
        cls.profissional = Profissional.objects.create(
            nome="Profissional Responsável",
            cpf="11144477735",
            password="hash-de-teste",
            cargo="Médica",
            unidade=cls.unidade,
        )
        cls.profissional.user_permissions.add(*permissoes)
        cls.outro_profissional = Profissional.objects.create(
            nome="Outro Profissional",
            cpf="16899535009",
            password="hash-de-teste",
            cargo="Médico",
            unidade=cls.unidade,
        )
        cls.outro_profissional.user_permissions.add(*permissoes)
        cls.profissional_sem_alteracao = Profissional.objects.create(
            nome="Profissional sem Alteração",
            cpf="93541134780",
            password="hash-de-teste",
            cargo="Biomédica",
            unidade=cls.unidade,
        )
        cls.profissional_sem_alteracao.user_permissions.add(
            Permission.objects.get(codename="view_exame")
        )
        cls.data = timezone.make_aware(datetime(2026, 10, 10, 14, 0))
        cls.agendamento = Agendamento.objects.create(
            usuario=cls.cidadao,
            unidade=cls.unidade,
            data=cls.data - timedelta(days=1),
        )

    def criar_exame(self, **alteracoes):
        dados = {
            "tipo": "Hemograma",
            "data": self.data,
            "status": Exame.Status.CONFIRMADO,
            "usuario": self.cidadao,
            "unidade": self.unidade,
            "profissional": self.profissional,
            "agendamento": self.agendamento,
        }
        dados.update(alteracoes)
        return Exame.objects.create(**dados)

    def test_detalhe_exibe_dados_sem_campos_de_edicao_estrutural(self):
        exame = self.criar_exame()
        self.client.force_login(self.profissional)

        resposta = self.client.get(
            reverse("exames:detalhe_profissional", args=[exame.pk])
        )

        self.assertContains(resposta, exame.tipo)
        self.assertContains(resposta, self.cidadao.nome)
        self.assertContains(resposta, self.unidade.nome)
        self.assertNotContains(resposta, 'name="tipo"')
        self.assertNotContains(resposta, 'name="usuario"')

    def test_profissional_nao_acessa_exame_de_terceiro(self):
        exame = self.criar_exame(profissional=self.outro_profissional)
        self.client.force_login(self.profissional)

        resposta = self.client.get(
            reverse("exames:detalhe_profissional", args=[exame.pk])
        )

        self.assertEqual(resposta.status_code, 404)

    def test_detalhe_exige_permissao_de_alteracao(self):
        exame = self.criar_exame(
            profissional=self.profissional_sem_alteracao
        )
        self.client.force_login(self.profissional_sem_alteracao)

        resposta = self.client.get(
            reverse("exames:detalhe_profissional", args=[exame.pk])
        )

        self.assertEqual(resposta.status_code, 403)

    def test_formulario_oferece_somente_transicoes_validas(self):
        exame = self.criar_exame()
        self.client.force_login(self.profissional)

        resposta = self.client.get(
            reverse("exames:detalhe_profissional", args=[exame.pk])
        )

        escolhas = dict(resposta.context["form"].fields["novo_status"].choices)
        self.assertEqual(
            set(escolhas),
            {Exame.Status.EM_ANALISE, Exame.Status.CANCELADO},
        )

    def test_profissional_avanca_e_cancela_exame(self):
        self.client.force_login(self.profissional)
        for novo_status in (
            Exame.Status.EM_ANALISE,
            Exame.Status.CANCELADO,
        ):
            with self.subTest(novo_status=novo_status):
                exame = self.criar_exame()
                resposta = self.client.post(
                    reverse("exames:detalhe_profissional", args=[exame.pk]),
                    {"novo_status": novo_status},
                )
                exame.refresh_from_db()
                self.assertEqual(resposta.status_code, 302)
                self.assertEqual(exame.status, novo_status)

    def test_post_falsificado_nao_executa_transicao_invalida(self):
        exame = self.criar_exame()
        self.client.force_login(self.profissional)

        resposta = self.client.post(
            reverse("exames:detalhe_profissional", args=[exame.pk]),
            {"novo_status": Exame.Status.RESULTADO_DISPONIVEL},
        )

        exame.refresh_from_db()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(exame.status, Exame.Status.CONFIRMADO)

    def test_resultado_e_obrigatorio_para_disponibilizacao(self):
        exame = self.criar_exame(status=Exame.Status.EM_ANALISE)
        self.client.force_login(self.profissional)

        resposta = self.client.post(
            reverse("exames:detalhe_profissional", args=[exame.pk]),
            {"novo_status": Exame.Status.RESULTADO_DISPONIVEL},
        )

        exame.refresh_from_db()
        self.assertContains(resposta, "Informe o resultado")
        self.assertEqual(exame.status, Exame.Status.EM_ANALISE)
        self.assertEqual(exame.resultado, "")

    def test_disponibiliza_resultado_com_pdf_e_notifica_cidadao(self):
        exame = self.criar_exame(status=Exame.Status.EM_ANALISE)
        documento = SimpleUploadedFile(
            "resultado.pdf",
            b"%PDF-1.4 documento de teste",
            content_type="application/pdf",
        )
        self.client.force_login(self.profissional)

        resposta = self.client.post(
            reverse("exames:detalhe_profissional", args=[exame.pk]),
            {
                "novo_status": Exame.Status.RESULTADO_DISPONIVEL,
                "resultado": "Resultado dentro dos valores de referência.",
                "documento_resultado": documento,
            },
        )

        exame.refresh_from_db()
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(exame.status, Exame.Status.RESULTADO_DISPONIVEL)
        self.assertEqual(
            exame.resultado,
            "Resultado dentro dos valores de referência.",
        )
        self.assertTrue(exame.documento_resultado.name.endswith(".pdf"))
        self.assertTrue(
            Notificacao.objects.filter(exame=exame, usuario=self.cidadao).exists()
        )

    def test_rejeita_arquivo_que_nao_e_pdf(self):
        exame = self.criar_exame(status=Exame.Status.EM_ANALISE)
        documento = SimpleUploadedFile(
            "resultado.txt",
            b"conteudo de texto",
            content_type="text/plain",
        )
        self.client.force_login(self.profissional)

        resposta = self.client.post(
            reverse("exames:detalhe_profissional", args=[exame.pk]),
            {
                "novo_status": Exame.Status.RESULTADO_DISPONIVEL,
                "resultado": "Resultado válido.",
                "documento_resultado": documento,
            },
        )

        exame.refresh_from_db()
        self.assertContains(resposta, "formato PDF")
        self.assertEqual(exame.status, Exame.Status.EM_ANALISE)

    def test_download_e_restrito_ao_cidadao_e_profissional_do_exame(self):
        exame = self.criar_exame(
            status=Exame.Status.RESULTADO_DISPONIVEL,
            resultado="Resultado válido.",
            documento_resultado=SimpleUploadedFile(
                "resultado.pdf",
                b"%PDF-1.4 documento de teste",
                content_type="application/pdf",
            ),
        )
        url = reverse("exames:documento_resultado", args=[exame.pk])

        for usuario in (self.cidadao, self.profissional):
            with self.subTest(usuario=usuario.nome):
                self.client.force_login(usuario)
                resposta = self.client.get(url)
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(resposta["Content-Type"], "application/pdf")

        self.client.force_login(self.outro_cidadao)
        self.assertEqual(self.client.get(url).status_code, 403)
