from django.contrib import admin
from django.test import RequestFactory, TestCase
from django.urls import reverse

from usuarios.admin import UsuarioAdmin, UsuarioCreationAdminForm
from usuarios.models import Usuario


class UsuarioAdminTests(TestCase):
    def setUp(self):
        self.superusuario = Usuario.objects.create_superuser(
            cpf="52998224725",
            nome="Administrador de Teste",
            password="senha-segura-123",
        )
        self.admin_model = UsuarioAdmin(Usuario, admin.site)
        self.request = RequestFactory().get("/admin/usuarios/usuario/")
        self.request.user = self.superusuario
        self.client.force_login(self.superusuario)

    def test_usuario_esta_registrado_no_admin(self):
        self.assertIn(Usuario, admin.site._registry)

    def test_admin_nao_permite_exclusao_fisica(self):
        self.assertFalse(self.admin_model.has_delete_permission(self.request))

    def test_formulario_de_criacao_aplica_hash_na_senha(self):
        formulario = UsuarioCreationAdminForm(
            data={
                "cpf": "11144477735",
                "nome": "Cidadã de Teste",
                "tipo": Usuario.Tipo.CIDADAO,
                "password1": "uma-senha-forte-123",
                "password2": "uma-senha-forte-123",
            }
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)
        usuario = formulario.save()
        self.assertTrue(usuario.check_password("uma-senha-forte-123"))

    def test_formulario_generico_nao_cria_profissional_sem_perfil(self):
        formulario = UsuarioCreationAdminForm(
            data={
                "cpf": "11144477735",
                "nome": "Profissional de Teste",
                "tipo": Usuario.Tipo.PROFISSIONAL,
                "password1": "uma-senha-forte-123",
                "password2": "uma-senha-forte-123",
            }
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn("tipo", formulario.errors)

    def test_usuario_sem_acesso_administrativo_nao_acessa_admin(self):
        usuario = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        self.client.force_login(usuario)

        resposta = self.client.get("/admin/usuarios/usuario/")

        self.assertEqual(resposta.status_code, 302)

    def test_admin_desativa_e_reativa_usuario(self):
        usuario = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Cidadã de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        url = reverse("admin:usuarios_usuario_changelist")
        selecao = {"_selected_action": [usuario.pk]}

        self.client.post(url, {**selecao, "action": "desativar_usuarios"})
        usuario.refresh_from_db()
        self.assertFalse(usuario.is_active)

        self.client.post(url, {**selecao, "action": "ativar_usuarios"})
        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)
