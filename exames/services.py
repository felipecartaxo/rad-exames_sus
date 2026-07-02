from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Agendamento, Exame


@transaction.atomic
def criar_agendamento_exame(
    *,
    usuario,
    unidade,
    profissional,
    tipo,
    data_agendamento,
    data_exame,
):
    agendamento = Agendamento.objects.create(
        usuario=usuario,
        unidade=unidade,
        data=data_agendamento,
    )
    exame = Exame.objects.create(
        tipo=tipo,
        data=data_exame,
        status=Exame.Status.CONFIRMADO,
        resultado="",
        usuario=usuario,
        unidade=unidade,
        profissional=profissional,
        agendamento=agendamento,
    )
    return exame


TRANSICOES_STATUS = {
    Exame.Status.CONFIRMADO: {
        Exame.Status.EM_ANALISE,
        Exame.Status.CANCELADO,
    },
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
def transicionar_status(
    exame,
    novo_status,
    *,
    resultado=None,
    documento_resultado=None,
):
    if not exame.pk:
        raise ValidationError(
            _("O exame deve estar salvo antes da transição de status."),
            code="exame_nao_persistido",
        )

    exame_bloqueado = Exame.objects.select_for_update().get(pk=exame.pk)
    validar_transicao_status(exame_bloqueado.status, novo_status)
    if (
        novo_status == Exame.Status.RESULTADO_DISPONIVEL
        and not (resultado or "").strip()
    ):
        raise ValidationError(
            {"resultado": _("Informe o resultado antes de disponibilizá-lo.")}
        )

    documento_anterior = exame_bloqueado.documento_resultado.name
    exame_bloqueado.status = novo_status
    campos_atualizados = ["status"]
    if novo_status == Exame.Status.RESULTADO_DISPONIVEL:
        exame_bloqueado.resultado = resultado.strip()
        campos_atualizados.append("resultado")
        if documento_resultado:
            exame_bloqueado.documento_resultado = documento_resultado
            campos_atualizados.append("documento_resultado")
    exame_bloqueado.save(update_fields=campos_atualizados)

    if novo_status == Exame.Status.RESULTADO_DISPONIVEL:
        from notificacoes.services import criar_notificacao_resultado_disponivel

        try:
            criar_notificacao_resultado_disponivel(exame_bloqueado)
        except Exception:
            if (
                documento_resultado
                and exame_bloqueado.documento_resultado.name
                != documento_anterior
            ):
                exame_bloqueado.documento_resultado.storage.delete(
                    exame_bloqueado.documento_resultado.name
                )
            raise

        if (
            documento_anterior
            and documento_anterior != exame_bloqueado.documento_resultado.name
        ):
            transaction.on_commit(
                lambda: exame_bloqueado.documento_resultado.storage.delete(
                    documento_anterior
                )
            )
    return exame_bloqueado
