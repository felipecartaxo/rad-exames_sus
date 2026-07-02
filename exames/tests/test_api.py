import tempfile
from datetime import datetime, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ExameApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.outro_cidadao = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Outra cidadã",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.servidor = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Servidor",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua Central, 100",
        )
        cls.outra_unidade = UnidadeSaude.objects.create(
            nome="Unidade Norte",
            endereco="Avenida Norte, 200",
        )
        cls.profissional = Profissional.objects.create(
            cpf="93541134780",
            nome="Profissional",
            cargo="Médica",
            unidade=cls.unidade,
        )
        cls.outro_profissional = Profissional.objects.create(
            cpf="39053344705",
            nome="Outro profissional",
            cargo="Médico",
            unidade=cls.outra_unidade,
        )
        cls.data_base = timezone.make_aware(
            datetime(2026, 10, 10, 14, 0)
        )

    def setUp(self):
        self.url = reverse("api_exames:lista")

    def criar_exame(
        self,
        *,
        usuario=None,
        profissional=None,
        unidade=None,
        **alteracoes,
    ):
        usuario = usuario or self.cidadao
        profissional = profissional or self.profissional
        unidade = unidade or self.unidade
        data = alteracoes.pop("data", self.data_base)
        agendamento = Agendamento.objects.create(
            usuario=usuario,
            unidade=unidade,
            data=data - timedelta(days=1),
        )
        dados = {
            "tipo": "Hemograma",
            "data": data,
            "status": Exame.Status.CONFIRMADO,
            "usuario": usuario,
            "unidade": unidade,
            "profissional": profissional,
            "agendamento": agendamento,
        }
        dados.update(alteracoes)
        return Exame.objects.create(**dados)

    def test_listagem_exige_autenticacao(self):
        resposta = self.client.get(self.url)

        self.assertIn(resposta.status_code, (401, 403))

    def test_cidadao_visualiza_somente_os_proprios_exames(self):
        proprio = self.criar_exame(tipo="Próprio")
        terceiro = self.criar_exame(
            usuario=self.outro_cidadao,
            tipo="Terceiro",
        )
        self.client.force_login(self.cidadao)

        dados = self.client.get(self.url).json()["results"]

        self.assertEqual([item["id"] for item in dados], [proprio.pk])
        self.assertNotIn(terceiro.pk, [item["id"] for item in dados])

    def test_profissional_visualiza_somente_exames_atribuidos(self):
        atribuido = self.criar_exame(tipo="Atribuído")
        terceiro = self.criar_exame(
            profissional=self.outro_profissional,
            tipo="Terceiro",
        )
        self.client.force_login(self.profissional)

        dados = self.client.get(self.url).json()["results"]

        self.assertEqual([item["id"] for item in dados], [atribuido.pk])
        self.assertNotIn(terceiro.pk, [item["id"] for item in dados])

    def test_servidor_visualiza_todos_os_exames(self):
        primeiro = self.criar_exame()
        segundo = self.criar_exame(usuario=self.outro_cidadao)
        self.client.force_login(self.servidor)

        dados = self.client.get(self.url).json()["results"]

        self.assertEqual(
            {item["id"] for item in dados},
            {primeiro.pk, segundo.pk},
        )

    def test_resposta_expoe_dados_essenciais_sem_cpf(self):
        exame = self.criar_exame(
            status=Exame.Status.RESULTADO_DISPONIVEL,
            resultado="Resultado disponível",
        )
        self.client.force_login(self.cidadao)

        item = self.client.get(self.url).json()["results"][0]

        self.assertEqual(item["id"], exame.pk)
        self.assertEqual(item["status_descricao"], "Resultado disponível")
        self.assertEqual(item["cidadao"]["nome"], self.cidadao.nome)
        self.assertEqual(item["unidade"]["nome"], self.unidade.nome)
        self.assertEqual(item["profissional"]["nome"], self.profissional.nome)
        self.assertNotIn("cpf", item["cidadao"])

    def test_listagem_e_paginada_e_ordenada(self):
        exames = [
            self.criar_exame(
                tipo=f"Exame {indice}",
                data=self.data_base + timedelta(hours=indice),
            )
            for indice in range(7)
        ]
        self.client.force_login(self.cidadao)

        primeira = self.client.get(self.url).json()
        segunda = self.client.get(self.url, {"page": 2}).json()

        self.assertEqual(primeira["count"], 7)
        self.assertEqual(len(primeira["results"]), 5)
        self.assertIsNotNone(primeira["next"])
        self.assertEqual(
            [item["id"] for item in primeira["results"]],
            [exame.pk for exame in reversed(exames[-5:])],
        )
        self.assertEqual(len(segunda["results"]), 2)

    def test_filtros_por_status_data_e_unidade(self):
        esperado = self.criar_exame(
            status=Exame.Status.EM_ANALISE,
            unidade=self.outra_unidade,
            profissional=self.outro_profissional,
            data=self.data_base + timedelta(hours=1),
        )
        self.criar_exame(status=Exame.Status.CONFIRMADO)
        self.client.force_login(self.cidadao)

        resposta = self.client.get(
            self.url,
            {
                "status": Exame.Status.EM_ANALISE,
                "data_inicio": self.data_base.isoformat(),
                "data_fim": (self.data_base + timedelta(hours=2)).isoformat(),
                "unidade": self.outra_unidade.pk,
            },
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [item["id"] for item in resposta.json()["results"]],
            [esperado.pk],
        )

    def test_filtro_invalido_retorna_400(self):
        self.client.force_login(self.cidadao)

        resposta = self.client.get(self.url, {"status": "DESCONHECIDO"})

        self.assertEqual(resposta.status_code, 400)

    def test_detalhe_respeita_isolamento_por_usuario(self):
        proprio = self.criar_exame()
        terceiro = self.criar_exame(usuario=self.outro_cidadao)
        self.client.force_login(self.cidadao)

        resposta_propria = self.client.get(
            reverse("api_exames:detalhe", args=[proprio.pk])
        )
        resposta_terceiro = self.client.get(
            reverse("api_exames:detalhe", args=[terceiro.pk])
        )

        self.assertEqual(resposta_propria.status_code, 200)
        self.assertEqual(resposta_terceiro.status_code, 404)

    def test_anexo_usa_url_protegida(self):
        exame = self.criar_exame(
            documento_resultado=SimpleUploadedFile(
                "resultado.pdf",
                b"%PDF-1.4 documento de teste",
                content_type="application/pdf",
            )
        )
        self.client.force_login(self.cidadao)

        item = self.client.get(
            reverse("api_exames:detalhe", args=[exame.pk])
        ).json()

        self.assertTrue(
            item["documento_resultado_url"].endswith(
                reverse("exames:documento_resultado", args=[exame.pk])
            )
        )
        self.assertNotIn("media_privada", item["documento_resultado_url"])
