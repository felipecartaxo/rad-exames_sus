from rest_framework import generics

from exames.models import Exame
from usuarios.models import Usuario

from .pagination import ExamePageNumberPagination
from .permissions import ExameApiPermission
from .serializers import (
    AtualizacaoExameApiSerializer,
    CriacaoExameApiSerializer,
    ExameSerializer,
    FiltroExameApiSerializer,
)


class ExameQuerysetMixin:
    permission_classes = (ExameApiPermission,)
    serializer_class = ExameSerializer

    def get_queryset(self):
        usuario = self.request.user
        queryset = Exame.objects.select_related(
            "usuario",
            "unidade",
            "profissional",
        )
        if usuario.tipo == Usuario.Tipo.CIDADAO:
            queryset = queryset.filter(usuario=usuario)
        elif usuario.tipo == Usuario.Tipo.PROFISSIONAL:
            queryset = queryset.filter(profissional_id=usuario.pk)
        elif usuario.tipo != Usuario.Tipo.SERVIDOR:
            queryset = queryset.none()
        return queryset.order_by("-data", "-pk")


class ExameListApiView(ExameQuerysetMixin, generics.ListCreateAPIView):
    pagination_class = ExamePageNumberPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CriacaoExameApiSerializer
        return ExameSerializer

    def filter_queryset(self, queryset):
        filtros = FiltroExameApiSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        dados = filtros.validated_data
        if dados.get("status"):
            queryset = queryset.filter(status=dados["status"])
        if dados.get("data_inicio"):
            queryset = queryset.filter(data__gte=dados["data_inicio"])
        if dados.get("data_fim"):
            queryset = queryset.filter(data__lte=dados["data_fim"])
        if dados.get("unidade"):
            queryset = queryset.filter(unidade_id=dados["unidade"])
        return queryset


class ExameDetailApiView(ExameQuerysetMixin, generics.RetrieveUpdateAPIView):
    http_method_names = ("get", "patch", "head", "options")

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return AtualizacaoExameApiSerializer
        return ExameSerializer
