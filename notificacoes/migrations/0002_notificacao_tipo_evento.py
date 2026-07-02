import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notificacoes", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="notificacao",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("ATRIBUICAO", "Exame atribuído"),
                    ("RESULTADO_DISPONIVEL", "Resultado disponível"),
                ],
                default="RESULTADO_DISPONIVEL",
                max_length=30,
                verbose_name="tipo de evento",
            ),
        ),
        migrations.AlterField(
            model_name="notificacao",
            name="exame",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="notificacoes",
                to="exames.exame",
                verbose_name="exame",
            ),
        ),
        migrations.AddConstraint(
            model_name="notificacao",
            constraint=models.UniqueConstraint(
                fields=("exame", "usuario", "tipo"),
                name="notificacao_evento_destinatario_unico",
            ),
        ),
    ]
