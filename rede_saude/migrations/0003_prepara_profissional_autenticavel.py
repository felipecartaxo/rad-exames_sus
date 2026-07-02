import django.db.models.deletion
import usuarios.managers
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0002_adiciona_tipo_profissional"),
        ("rede_saude", "0002_profissional"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProfissionalNovo",
            fields=[
                (
                    "usuario_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("cargo", models.CharField(max_length=100, verbose_name="cargo")),
                (
                    "especialidade",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="especialidade",
                    ),
                ),
                (
                    "unidade",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="profissionais_novos",
                        to="rede_saude.unidadesaude",
                        verbose_name="unidade de saúde",
                    ),
                ),
            ],
            options={
                "verbose_name": "profissional",
                "verbose_name_plural": "profissionais",
            },
            bases=("usuarios.usuario",),
            managers=[("objects", usuarios.managers.UsuarioManager())],
        ),
    ]
