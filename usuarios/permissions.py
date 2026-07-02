from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import Usuario


class ServidorAutorizadoMixin(AccessMixin):
    permission_required = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )

        permissoes = self.permission_required
        if isinstance(permissoes, str):
            permissoes = (permissoes,)
        autorizado = (
            request.user.tipo == Usuario.Tipo.SERVIDOR
            and permissoes
            and request.user.has_perms(permissoes)
        )
        if not autorizado:
            raise PermissionDenied(
                _("Você não tem permissão para acessar esta página.")
            )
        return super().dispatch(request, *args, **kwargs)
