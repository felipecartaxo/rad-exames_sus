from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from rede_saude.admin import ProfissionalAdmin, UnidadeSaudeAdmin
from rede_saude.forms import ProfissionalAdminForm
from rede_saude.models import Profissional, UnidadeSaude


Usuario = get_user_model()


class RedeSaudeAdminTests(TestCase):
    def setUp(self):
        self.superusuario = Usuario.objects.create_superuser(
            cpf="52998224725",
            nome="Administrador de Teste",
            password="senha-segura-123",
        )
        self.client.force_login(self.superusuario)
        self.unidade_ativa = UnidadeSaude.objects.create(
            nome="Unidade Ativa",
            endereco="Rua Ativa, 100",
        )
        self.unidade_inativa = UnidadeSaude.objects.create(
            nome="Unidade Inativa",
            endereco="Rua Inativa, 200",
            ativo=False,
        )
        self.request = RequestFactory().get("/admin/rede_saude/")
        self.request.user = self.superusuario

    def test_modelos_estao_registrados_no_admin(self):
        self.assertIn(UnidadeSaude, admin.site._registry)
        self.assertIn(Profissional, admin.site._registry)

    def test_admins_nao_permitem_exclusao_fisica(self):
        admins = (
            UnidadeSaudeAdmin(UnidadeSaude, admin.site),
            ProfissionalAdmin(Profissional, admin.site),
        )

        for admin_model in admins:
            with self.subTest(modelo=admin_model.model.__name__):
                self.assertFalse(admin_model.has_delete_permission(self.request))

    def test_novo_profissional_lista_apenas_unidades_ativas(self):
        formulario = ProfissionalAdminForm()

        self.assertQuerySetEqual(
            formulario.fields["unidade"].queryset,
            [self.unidade_ativa],
        )

    def test_edicao_preserva_unidade_inativa_atual_como_opcao(self):
        profissional = Profissional.objects.create(
            nome="Profissional de Teste",
            cpf="11144477735",
            cargo="Médico",
            unidade=self.unidade_inativa,
        )

        formulario = ProfissionalAdminForm(instance=profissional)

        self.assertIn(
            self.unidade_inativa,
            formulario.fields["unidade"].queryset,
        )

    def test_cadastro_de_profissional_valida_e_normaliza_cpf(self):
        formulario = ProfissionalAdminForm(
            data={
                "nome": "Profissional de Teste",
                "cpf": "111.444.777-35",
                "cargo": "Médico",
                "especialidade": "Clínica geral",
                "unidade": self.unidade_ativa.pk,
                "ativo": True,
            }
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)
        profissional = formulario.save()
        self.assertEqual(profissional.cpf, "11144477735")

    def test_desativacao_de_unidade_exige_confirmacao(self):
        url = reverse("admin:rede_saude_unidadesaude_changelist")
        dados = {
            "action": "desativar_unidades",
            "_selected_action": [self.unidade_ativa.pk],
        }

        resposta = self.client.post(url, dados)
        self.unidade_ativa.refresh_from_db()

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Confirmar desativação")
        self.assertTrue(self.unidade_ativa.ativo)

        resposta = self.client.post(url, {**dados, "confirmar": "1"})
        self.unidade_ativa.refresh_from_db()

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(self.unidade_ativa.ativo)

    def test_admin_desativa_e_reativa_profissional(self):
        profissional = Profissional.objects.create(
            nome="Profissional de Teste",
            cpf="11144477735",
            cargo="Médico",
            unidade=self.unidade_ativa,
        )
        url = reverse("admin:rede_saude_profissional_changelist")
        selecao = {"_selected_action": [profissional.pk]}

        self.client.post(
            url,
            {**selecao, "action": "desativar_profissionais"},
        )
        profissional.refresh_from_db()
        self.assertFalse(profissional.ativo)

        self.client.post(
            url,
            {**selecao, "action": "ativar_profissionais"},
        )
        profissional.refresh_from_db()
        self.assertTrue(profissional.ativo)
