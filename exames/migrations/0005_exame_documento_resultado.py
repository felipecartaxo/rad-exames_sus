import exames.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("exames", "0004_substitui_relacao_profissional"),
    ]

    operations = [
        migrations.AddField(
            model_name="exame",
            name="documento_resultado",
            field=models.FileField(
                blank=True,
                default="",
                upload_to="resultados/",
                validators=[exames.validators.validar_documento_resultado],
                verbose_name="documento do resultado",
            ),
        ),
    ]
