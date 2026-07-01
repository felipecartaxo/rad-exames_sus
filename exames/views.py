from django.views.generic.list import ListView

from .models import Exame
from .permissions import CidadaoAutenticadoMixin


class ExameListView(CidadaoAutenticadoMixin, ListView):
    model = Exame
    template_name = "exames/lista.html"
    context_object_name = "exames"
    paginate_by = 5

    def get_queryset(self):
        return (
            Exame.objects.filter(usuario=self.request.user)
            .select_related("unidade")
            .order_by("-data", "-pk")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class ExameHistoricoView(CidadaoAutenticadoMixin, ListView):
    model = Exame
    template_name = "exames/historico.html"
    context_object_name = "exames"
    paginate_by = 5

    def get_queryset(self):
        return (
            Exame.objects.filter(usuario=self.request.user)
            .select_related("unidade", "profissional")
            .order_by("-data", "-pk")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto
