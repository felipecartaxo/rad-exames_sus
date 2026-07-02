from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def migrar_profissionais(apps, schema_editor):
    Usuario = apps.get_model("usuarios", "Usuario")
    ProfissionalLegado = apps.get_model("rede_saude", "Profissional")
    ProfissionalNovo = apps.get_model("rede_saude", "ProfissionalNovo")
    Exame = apps.get_model("exames", "Exame")

    profissionais = list(ProfissionalLegado.objects.order_by("pk"))
    cpfs = [profissional.cpf for profissional in profissionais]
    conflitos = list(
        Usuario.objects.filter(cpf__in=cpfs).values_list("cpf", flat=True)
    )
    if conflitos:
        raise RuntimeError(
            "Não foi possível migrar profissionais: existem CPFs já "
            f"cadastrados em Usuario: {', '.join(sorted(conflitos))}."
        )

    for profissional in profissionais:
        usuario = Usuario.objects.create(
            nome=profissional.nome,
            cpf=profissional.cpf,
            tipo="PROFISSIONAL",
            password=make_password(None),
            is_active=profissional.ativo,
            is_staff=False,
            is_superuser=False,
        )
        ProfissionalNovo.objects.create(
            usuario_ptr_id=usuario.pk,
            cargo=profissional.cargo,
            especialidade=profissional.especialidade,
            unidade_id=profissional.unidade_id,
        )
        Exame.objects.filter(profissional_id=profissional.pk).update(
            profissional_novo_id=usuario.pk
        )


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0002_adiciona_tipo_profissional"),
        ("rede_saude", "0003_prepara_profissional_autenticavel"),
        ("exames", "0002_exame"),
    ]

    operations = [
        migrations.AddField(
            model_name="exame",
            name="profissional_novo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="exames_atribuidos",
                to="rede_saude.profissionalnovo",
                verbose_name="profissional",
            ),
        ),
        migrations.RunPython(migrar_profissionais, migrations.RunPython.noop),
    ]
