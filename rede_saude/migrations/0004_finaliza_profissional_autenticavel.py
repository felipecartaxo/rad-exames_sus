import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rede_saude", "0003_prepara_profissional_autenticavel"),
        ("exames", "0004_substitui_relacao_profissional"),
    ]

    operations = [
        migrations.DeleteModel(name="Profissional"),
        migrations.RenameModel(
            old_name="ProfissionalNovo",
            new_name="Profissional",
        ),
        migrations.AlterField(
            model_name="profissional",
            name="unidade",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="profissionais",
                to="rede_saude.unidadesaude",
                verbose_name="unidade de saúde",
            ),
        ),
    ]
