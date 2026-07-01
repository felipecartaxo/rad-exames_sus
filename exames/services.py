from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Exame


TRANSICOES_STATUS = {
    Exame.Status.AGENDADO: {
        Exame.Status.AGUARDANDO_CONFIRMACAO,
        Exame.Status.CANCELADO,
    },
    Exame.Status.AGUARDANDO_CONFIRMACAO: {
        Exame.Status.CONFIRMADO,
        Exame.Status.CANCELADO,
    },
    Exame.Status.CONFIRMADO: {
        Exame.Status.REALIZADO,
        Exame.Status.CANCELADO,
    },
    Exame.Status.REALIZADO: {Exame.Status.EM_ANALISE},
    Exame.Status.EM_ANALISE: {Exame.Status.RESULTADO_DISPONIVEL},
    Exame.Status.RESULTADO_DISPONIVEL: set(),
    Exame.Status.CANCELADO: set(),
}


def validar_transicao_status(status_atual, novo_status):
    if novo_status not in TRANSICOES_STATUS.get(status_atual, set()):
        raise ValidationError(
            _("Transição de status de %(atual)s para %(novo)s não permitida."),
            code="transicao_status_invalida",
            params={"atual": status_atual, "novo": novo_status},
        )


@transaction.atomic
def transicionar_status(exame, novo_status):
    if not exame.pk:
        raise ValidationError(
            _("O exame deve estar salvo antes da transição de status."),
            code="exame_nao_persistido",
        )

    exame_bloqueado = Exame.objects.select_for_update().get(pk=exame.pk)
    validar_transicao_status(exame_bloqueado.status, novo_status)
    exame_bloqueado.status = novo_status
    exame_bloqueado.save(update_fields=["status"])
    if novo_status == Exame.Status.RESULTADO_DISPONIVEL:
        from notificacoes.services import criar_notificacao_resultado_disponivel

        criar_notificacao_resultado_disponivel(exame_bloqueado)
    return exame_bloqueado
