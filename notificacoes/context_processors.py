from usuarios.models import Usuario

from .models import Notificacao


def notificacoes_nao_lidas(request):
    quantidade = 0
    if (
        request.user.is_authenticated
        and request.user.tipo == Usuario.Tipo.CIDADAO
    ):
        quantidade = Notificacao.objects.filter(
            usuario=request.user,
            lida=False,
        ).count()
    return {"notificacoes_nao_lidas": quantidade}

