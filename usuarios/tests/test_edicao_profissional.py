from django.test import TestCase
from django.urls import reverse

from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


class EdicaoProfissionalServidorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.unidade = UnidadeSaude.objects.create(
            nome="Unidade Central",
            endereco="Rua Central, 100",
        )
        cls.outra_unidade = UnidadeSaude.objects.create(
            nome="Unidade Norte",
            endereco="Avenida Norte, 200",
        )
        cls.servidor = Usuario.objects.create_user(
            cpf="52998224725",
            nome="Servidor",
            tipo=Usuario.Tipo.SERVIDOR,
            password="senha-segura-123",
        )
        cls.cidadao = Usuario.objects.create_user(
            cpf="12345678909",
            nome="Cidadão",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )
        cls.profissional = Profissional.objects.create(
            cpf="93541134780",
            nome="Profissional original",
            tipo=Usuario.Tipo.PROFISSIONAL,
            cargo="Médica",
            especialidade="Clínica geral",
            unidade=cls.unidade,
        )
        cls.profissional.set_password("senha-segura-123")
        cls.profissional.save()

    def setUp(self):
        self.url = reverse(
            "usuarios_lista:editar_profissional",
            args=[self.profissional.pk],
        )

    def test_acesso_exige_perfil_servidor(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.client.force_login(self.cidadao)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.client.force_login(self.servidor)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_servidor_edita_dados_do_profissional(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            {
                "nome": "Profissional atualizada",
                "cpf": "935.411.347-80",
                "cargo": "Médica reguladora",
                "especialidade": "Cardiologia",
                "unidade": self.outra_unidade.pk,
                "password1": "",
                "password2": "",
            },
        )

        self.assertRedirects(resposta, reverse("usuarios_lista:lista"))
        self.profissional.refresh_from_db()
        self.assertEqual(self.profissional.nome, "Profissional atualizada")
        self.assertEqual(self.profissional.cpf, "93541134780")
        self.assertEqual(self.profissional.cargo, "Médica reguladora")
        self.assertEqual(self.profissional.especialidade, "Cardiologia")
        self.assertEqual(self.profissional.unidade, self.outra_unidade)
        self.assertTrue(
            self.profissional.check_password("senha-segura-123")
        )

    def test_servidor_pode_redefinir_senha_do_profissional(self):
        self.client.force_login(self.servidor)

        resposta = self.client.post(
            self.url,
            {
                "nome": self.profissional.nome,
                "cpf": self.profissional.cpf,
                "cargo": self.profissional.cargo,
                "especialidade": self.profissional.especialidade,
                "unidade": self.profissional.unidade_id,
                "password1": "nova-senha-segura-456",
                "password2": "nova-senha-segura-456",
            },
        )

        self.assertRedirects(resposta, reverse("usuarios_lista:lista"))
        self.profissional.refresh_from_db()
        self.assertTrue(
            self.profissional.check_password("nova-senha-segura-456")
        )

    def test_formulario_nao_permite_alterar_situacao(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(self.url)

        self.assertNotIn("is_active", resposta.context["form"].fields)

    def test_listagem_exibe_acao_de_edicao_para_profissional_real(self):
        self.client.force_login(self.servidor)

        resposta = self.client.get(reverse("usuarios_lista:lista"))

        self.assertContains(resposta, self.url)
