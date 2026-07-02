from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from usuarios.models import Usuario


class CidadaoAutenticadoMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                "usuarios:login",
            )
        if request.user.tipo != Usuario.Tipo.CIDADAO:
            raise PermissionDenied(
                _("Você não tem permissão para acessar esta página.")
            )
        return super().dispatch(request, *args, **kwargs)


class ProfissionalAutorizadoMixin(View):
    permission_required = "exames.view_exame"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                "usuarios:login",
            )
        autorizado = (
            request.user.tipo == Usuario.Tipo.PROFISSIONAL
            and request.user.has_perm(self.permission_required)
        )
        if not autorizado:
            raise PermissionDenied(
                _("Você não tem permissão para acessar esta página.")
            )
        return super().dispatch(request, *args, **kwargs)
