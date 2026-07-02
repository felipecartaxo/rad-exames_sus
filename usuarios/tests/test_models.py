from django.contrib.auth import get_user_model
from django.test import TestCase


Usuario = get_user_model()


class UsuarioManagerTests(TestCase):
    def test_create_user_normaliza_cpf_e_protege_senha(self):
        usuario = Usuario.objects.create_user(
            cpf="529.982.247-25",
            nome="  Maria da Silva  ",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )

        self.assertEqual(usuario.cpf, "52998224725")
        self.assertEqual(usuario.nome, "Maria da Silva")
        self.assertTrue(usuario.check_password("senha-segura-123"))
        self.assertNotEqual(usuario.password, "senha-segura-123")

    def test_get_by_natural_key_aceita_cpf_formatado(self):
        criado = Usuario.objects.create_user(
            cpf="11144477735",
            nome="Pessoa de Teste",
            tipo=Usuario.Tipo.CIDADAO,
            password="senha-segura-123",
        )

        encontrado = Usuario.objects.get_by_natural_key("111.444.777-35")

        self.assertEqual(encontrado, criado)

    def test_create_user_exige_cpf(self):
        with self.assertRaisesMessage(ValueError, "O CPF é obrigatório."):
            Usuario.objects.create_user(
                cpf="",
                nome="Pessoa de Teste",
                tipo=Usuario.Tipo.CIDADAO,
            )

    def test_create_user_exige_nome(self):
        with self.assertRaisesMessage(ValueError, "O nome é obrigatório."):
            Usuario.objects.create_user(
                cpf="11144477735",
                nome=" ",
                tipo=Usuario.Tipo.CIDADAO,
            )

    def test_create_user_rejeita_tipo_nao_autorizado(self):
        with self.assertRaisesMessage(ValueError, "O tipo de usuário é inválido."):
            Usuario.objects.create_user(
                cpf="11144477735",
                nome="Pessoa de Teste",
                tipo="OUTRO",
            )

    def test_create_superuser_define_convencoes_administrativas(self):
        usuario = Usuario.objects.create_superuser(
            cpf="123.456.789-09",
            nome="Administrador de Teste",
            password="senha-segura-123",
        )

        self.assertEqual(usuario.tipo, Usuario.Tipo.SERVIDOR)
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)
        self.assertTrue(usuario.is_active)


class UsuarioModelTests(TestCase):
    def test_cpf_e_identificador_de_autenticacao(self):
        self.assertEqual(Usuario.USERNAME_FIELD, "cpf")
        self.assertEqual(Usuario.REQUIRED_FIELDS, ["nome"])

    def test_tipo_possui_somente_valores_autorizados(self):
        self.assertEqual(
            set(Usuario.Tipo.values),
            {"CIDADAO", "SERVIDOR", "PROFISSIONAL"},
        )
