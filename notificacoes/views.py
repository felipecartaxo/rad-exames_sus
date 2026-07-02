from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.list import ListView

from usuarios.models import Usuario

from .models import Notificacao


class DestinatarioNotificacaoMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), "usuarios:login")
        if request.user.tipo not in (
            Usuario.Tipo.CIDADAO,
            Usuario.Tipo.PROFISSIONAL,
        ):
            raise PermissionDenied(
                _("Você não tem permissão para acessar esta página.")
            )
        return super().dispatch(request, *args, **kwargs)


class NotificacaoListView(DestinatarioNotificacaoMixin, ListView):
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


class MarcarNotificacoesLidasView(DestinatarioNotificacaoMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        quantidade = Notificacao.objects.filter(
            usuario=request.user,
            lida=False,
        ).update(lida=True)
        if quantidade:
            messages.success(request, _("Notificações marcadas como lidas."))
        return redirect("notificacoes:lista")
