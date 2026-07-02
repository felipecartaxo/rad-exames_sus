from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework.reverse import reverse

from exames.models import Exame
from exames.services import (
    TRANSICOES_STATUS,
    criar_agendamento_exame,
    transicionar_status,
)
from exames.validators import validar_documento_resultado
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


class CriacaoExameApiSerializer(serializers.Serializer):
    usuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(
            tipo=Usuario.Tipo.CIDADAO,
            is_active=True,
        )
    )
    unidade = serializers.PrimaryKeyRelatedField(
        queryset=UnidadeSaude.objects.filter(ativo=True)
    )
    profissional = serializers.PrimaryKeyRelatedField(
        queryset=Profissional.objects.filter(is_active=True)
    )
    tipo = serializers.CharField(max_length=150)
    data_agendamento = serializers.DateTimeField()
    data_exame = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["data_exame"] <= attrs["data_agendamento"]:
            raise serializers.ValidationError(
                {
                    "data_exame": (
                        "A data do exame deve ser posterior à data "
                        "do agendamento."
                    )
                }
            )
        return attrs

    def create(self, validated_data):
        return criar_agendamento_exame(**validated_data)

    def to_representation(self, instance):
        return ExameSerializer(instance, context=self.context).data


class AtualizacaoExameApiSerializer(serializers.Serializer):
    novo_status = serializers.ChoiceField(choices=Exame.Status.choices)
    resultado = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
    )
    documento_resultado = serializers.FileField(
        required=False,
        validators=[validar_documento_resultado],
    )

    def validate(self, attrs):
        exame = self.instance
        novo_status = attrs["novo_status"]
        if novo_status not in TRANSICOES_STATUS.get(exame.status, set()):
            raise serializers.ValidationError(
                {"novo_status": "Transição de status não permitida."}
            )
        resultado = (attrs.get("resultado") or "").strip()
        documento = attrs.get("documento_resultado")
        if novo_status == Exame.Status.RESULTADO_DISPONIVEL:
            if not resultado:
                raise serializers.ValidationError(
                    {"resultado": "Informe o resultado antes de disponibilizá-lo."}
                )
            attrs["resultado"] = resultado
        elif resultado or documento:
            raise serializers.ValidationError(
                "Resultado e documento só podem ser enviados ao "
                "disponibilizar o resultado."
            )
        return attrs

    def update(self, instance, validated_data):
        try:
            return transicionar_status(
                instance,
                validated_data["novo_status"],
                resultado=validated_data.get("resultado"),
                documento_resultado=validated_data.get("documento_resultado"),
            )
        except DjangoValidationError as erro:
            if hasattr(erro, "message_dict"):
                raise serializers.ValidationError(erro.message_dict) from erro
            raise serializers.ValidationError(erro.messages) from erro

    def to_representation(self, instance):
        return ExameSerializer(instance, context=self.context).data
