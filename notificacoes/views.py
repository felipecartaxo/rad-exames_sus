from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.list import ListView

from exames.permissions import CidadaoAutenticadoMixin

from .models import Notificacao


class NotificacaoListView(CidadaoAutenticadoMixin, ListView):
    model = Notificacao
    template_name = "notificacoes/lista.html"
    context_object_name = "notificacoes"
    paginate_by = 5

    def get_queryset(self):
        return (
            Notificacao.objects.filter(usuario=self.request.user)
            .select_related("exame")
            .order_by("-pk")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class MarcarNotificacoesLidasView(CidadaoAutenticadoMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        quantidade = Notificacao.objects.filter(
            usuario=request.user,
            lida=False,
        ).update(lida=True)
        if quantidade:
            messages.success(request, _("Notificações marcadas como lidas."))
        return redirect("notificacoes:lista")

