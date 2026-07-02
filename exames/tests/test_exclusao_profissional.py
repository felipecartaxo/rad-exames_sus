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
class ExclusaoExameProfissionalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua Central, 100",
        )
        permissoes = Permission.objects.filter(codename="view_exame")
        cls.profissional = Profissional.objects.create(
            nome="Profissional responsável",
            cpf="11144477735",
            cargo="Médica",
            unidade=cls.unidade,
        )
        cls.profissional.user_permissions.add(*permissoes)
        cls.outro_profissional = Profissional.objects.create(
            nome="Outro profissional",
            cpf="16899535009",
            cargo="Médico",
            unidade=cls.unidade,
        )
        cls.outro_profissional.user_permissions.add(*permissoes)
        cls.profissional_sem_permissao = Profissional.objects.create(
            nome="Profissional sem permissão",
            cpf="93541134780",
            cargo="Biomédica",
            unidade=cls.unidade,
        )
        cls.data = timezone.make_aware(datetime(2026, 10, 10, 14, 0))

    def criar_exame(self, profissional=None, documento=False):
        agendamento = Agendamento.objects.create(
            usuario=self.cidadao,
            unidade=self.unidade,
            data=self.data - timedelta(days=1),
        )
        dados = {
            "tipo": "Hemograma",
            "data": self.data,
            "status": Exame.Status.RESULTADO_DISPONIVEL,
            "resultado": "Resultado do exame",
            "usuario": self.cidadao,
            "unidade": self.unidade,
            "profissional": profissional or self.profissional,
            "agendamento": agendamento,
        }
        if documento:
            dados["documento_resultado"] = SimpleUploadedFile(
                "resultado.pdf",
                b"%PDF-1.4 documento de teste",
                content_type="application/pdf",
            )
        return Exame.objects.create(**dados)

    def test_tela_exige_perfil_permissao_e_vinculo(self):
        exame = self.criar_exame()
        url = reverse("exames:excluir_profissional", args=[exame.pk])

        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.profissional_sem_permissao)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.outro_profissional)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.profissional)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_get_apenas_apresenta_confirmacao(self):
        exame = self.criar_exame()
        self.client.force_login(self.profissional)

        resposta = self.client.get(
            reverse("exames:excluir_profissional", args=[exame.pk])
        )

        self.assertContains(resposta, "Esta ação não pode ser desfeita")
        self.assertTrue(Exame.objects.filter(pk=exame.pk).exists())

    def test_post_exclui_exame_notificacao_agendamento_e_pdf(self):
        exame = self.criar_exame(documento=True)
        agendamento_id = exame.agendamento_id
        nome_documento = exame.documento_resultado.name
        armazenamento = exame.documento_resultado.storage
        Notificacao.objects.create(
            usuario=self.cidadao,
            exame=exame,
            mensagem="Resultado disponível.",
        )
        self.client.force_login(self.profissional)

        with self.captureOnCommitCallbacks(execute=True):
            resposta = self.client.post(
                reverse("exames:excluir_profissional", args=[exame.pk])
            )

        self.assertRedirects(resposta, reverse("exames:lista_profissional"))
        self.assertFalse(Exame.objects.filter(pk=exame.pk).exists())
        self.assertFalse(
            Agendamento.objects.filter(pk=agendamento_id).exists()
        )
        self.assertFalse(Notificacao.objects.filter(exame_id=exame.pk).exists())
        self.assertFalse(armazenamento.exists(nome_documento))
