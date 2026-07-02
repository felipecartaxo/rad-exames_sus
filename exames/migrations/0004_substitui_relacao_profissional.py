import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("exames", "0003_migra_profissionais"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="exame",
            name="profissional",
        ),
        migrations.RenameField(
            model_name="exame",
            old_name="profissional_novo",
            new_name="profissional",
        ),
        migrations.AlterField(
            model_name="exame",
            name="profissional",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="exames_atribuidos",
                to="rede_saude.profissionalnovo",
                verbose_name="profissional",
            ),
        ),
    ]
