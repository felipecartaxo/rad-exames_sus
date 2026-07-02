from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("CIDADAO", "Cidadão"),
                    ("SERVIDOR", "Servidor"),
                    ("PROFISSIONAL", "Profissional"),
                ],
                max_length=12,
                verbose_name="tipo",
            ),
        ),
    ]
