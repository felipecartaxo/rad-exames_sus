from rest_framework import serializers
from rest_framework.reverse import reverse

from exames.models import Exame
from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario


class UsuarioResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ("id", "nome")


class UnidadeSaudeResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeSaude
        fields = ("id", "nome")


class ProfissionalResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profissional
        fields = ("id", "nome")


class ExameSerializer(serializers.ModelSerializer):
    status_descricao = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )
    cidadao = UsuarioResumoSerializer(source="usuario", read_only=True)
    unidade = UnidadeSaudeResumoSerializer(read_only=True)
    profissional = ProfissionalResumoSerializer(read_only=True)
    documento_resultado_url = serializers.SerializerMethodField()

    class Meta:
        model = Exame
        fields = (
            "id",
            "tipo",
            "data",
            "status",
            "status_descricao",
            "resultado",
            "cidadao",
            "unidade",
            "profissional",
            "documento_resultado_url",
        )

    def get_documento_resultado_url(self, exame):
        if not exame.documento_resultado:
            return None
        request = self.context["request"]
        caminho = reverse(
            "exames:documento_resultado",
            args=[exame.pk],
            request=request,
        )
        return caminho


class FiltroExameApiSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=Exame.Status.choices,
        required=False,
    )
    data_inicio = serializers.DateTimeField(required=False)
    data_fim = serializers.DateTimeField(required=False)
    unidade = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        inicio = attrs.get("data_inicio")
        fim = attrs.get("data_fim")
        if inicio and fim and fim < inicio:
            raise serializers.ValidationError(
                {"data_fim": "A data final deve ser posterior à data inicial."}
            )
        return attrs
