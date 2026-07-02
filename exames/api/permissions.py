from rest_framework.permissions import SAFE_METHODS, BasePermission

from usuarios.models import Usuario


class ExameApiPermission(BasePermission):
    message = "Você não tem permissão para realizar esta operação."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return (
            request.method == "POST"
            and request.user.tipo == Usuario.Tipo.SERVIDOR
            and request.user.has_perms(
                ("exames.add_agendamento", "exames.add_exame")
            )
        )
