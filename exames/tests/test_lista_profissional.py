from datetime import datetime, timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from exames.models import Agendamento, Exame
from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


class ExameProfissionalListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cidadao = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Cidadã de Teste",
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
            endereco="Rua Principal, 10",
        )
        cls.profissional = Profissional.objects.create(
            nome="Profissional Responsável",
            cpf="11144477735",
            password="hash-de-teste",
            cargo="Médica",
            unidade=cls.unidade,
        )
        cls.outro_profissional = Profissional.objects.create(
            nome="Outro Profissional",
            cpf="16899535009",
            password="hash-de-teste",
            cargo="Médico",
            unidade=cls.unidade,
        )
        permissao = Permission.objects.get(codename="view_exame")
        cls.profissional.user_permissions.add(permissao)
        cls.outro_profissional.user_permissions.add(permissao)
        cls.profissional_sem_permissao = Profissional.objects.create(
            nome="Profissional sem Permissão",
            cpf="93541134780",
            password="hash-de-teste",
            cargo="Biomédica",
            unidade=cls.unidade,
        )
        cls.data_base = timezone.make_aware(datetime(2026, 9, 20, 14, 0))
        cls.agendamento = Agendamento.objects.create(
            usuario=cls.cidadao,
            unidade=cls.unidade,
            data=cls.data_base - timedelta(days=1),
        )

    def setUp(self):
        self.url = reverse("exames:lista_profissional")

    def criar_exame(self, profissional=None, **alteracoes):
        dados = {
            "tipo": "Hemograma",
            "data": self.data_base,
            "status": Exame.Status.CONFIRMADO,
            "usuario": self.cidadao,
            "unidade": self.unidade,
            "profissional": profissional or self.profissional,
            "agendamento": self.agendamento,
        }
        dados.update(alteracoes)
        return Exame.objects.create(**dados)

    def test_usuario_anonimo_e_direcionado_ao_login(self):
        resposta = self.client.get(self.url)

        self.assertRedirects(
            resposta,
            f"{reverse('usuarios:login')}?next={self.url}",
        )

    def test_acesso_exige_perfil_profissional_e_permissao(self):
        for usuario in (
            self.cidadao,
            self.servidor,
            self.profissional_sem_permissao,
        ):
            with self.subTest(usuario=usuario.nome):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_profissional_visualiza_somente_exames_atribuidos(self):
        proprio = self.criar_exame(tipo="Exame próprio")
        terceiro = self.criar_exame(
            profissional=self.outro_profissional,
            tipo="Exame de terceiro",
        )
        self.client.force_login(self.profissional)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, proprio.tipo)
        self.assertNotContains(resposta, terceiro.tipo)
        self.assertQuerySetEqual(resposta.context["exames"], [proprio])

    def test_lista_apresenta_dados_essenciais(self):
        exame = self.criar_exame(status=Exame.Status.CONFIRMADO)
        self.client.force_login(self.profissional)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, exame.tipo)
        self.assertContains(resposta, exame.get_status_display())
        self.assertContains(resposta, self.cidadao.nome)
        self.assertContains(resposta, self.unidade.nome)

    def test_lista_exibe_estado_vazio(self):
        self.client.force_login(self.profissional)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Nenhum exame atribuído")

    def test_lista_e_paginada_e_ordenada(self):
        exames = [
            self.criar_exame(
                tipo=f"Exame {indice}",
                data=self.data_base + timedelta(minutes=indice),
            )
            for indice in range(7)
        ]
        self.client.force_login(self.profissional)

        primeira = self.client.get(self.url)
        segunda = self.client.get(self.url, {"page": 2})

        self.assertEqual(len(primeira.context["exames"]), 5)
        self.assertQuerySetEqual(
            primeira.context["exames"],
            list(reversed(exames[-5:])),
        )
        self.assertEqual(len(segunda.context["exames"]), 2)

    def test_login_redireciona_profissional_para_lista(self):
        self.profissional.set_password("senha-segura-123")
        self.profissional.save()

        resposta = self.client.post(
            reverse("usuarios:login"),
            {
                "username": self.profissional.cpf,
                "password": "senha-segura-123",
            },
        )

        self.assertRedirects(resposta, self.url)

    def test_cabecalho_exibe_link_da_area_profissional(self):
        self.client.force_login(self.profissional)

        resposta = self.client.get(self.url)

        self.assertContains(resposta, "Exames atribuídos")
