from django.db import migrations, models


def migrar_status_legados(apps, schema_editor):
    Exame = apps.get_model("exames", "Exame")
    Exame.objects.filter(
        status__in=("AGENDADO", "AGUARDANDO_CONFIRMACAO")
    ).update(status="CONFIRMADO")
    Exame.objects.filter(status="REALIZADO").update(status="EM_ANALISE")


class Migration(migrations.Migration):
    dependencies = [
        ("exames", "0005_exame_documento_resultado"),
    ]

    operations = [
        migrations.RunPython(migrar_status_legados, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="exame",
            name="status",
            field=models.CharField(
                choices=[
                    ("CONFIRMADO", "Confirmado"),
                    ("EM_ANALISE", "Em análise"),
                    ("RESULTADO_DISPONIVEL", "Resultado disponível"),
                    ("CANCELADO", "Cancelado"),
                ],
                max_length=23,
                verbose_name="status",
            ),
        ),
    ]
