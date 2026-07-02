from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from exames.models import Exame

from .models import Notificacao


def criar_notificacao_exame_atribuido(exame):
    notificacao, criada = Notificacao.objects.get_or_create(
        exame=exame,
        usuario=exame.profissional,
        tipo=Notificacao.TipoEvento.ATRIBUICAO,
        defaults={
            "mensagem": _(
                "O exame %(tipo)s foi atribuído a você. "
                "Consulte os detalhes para acompanhar o atendimento."
            )
            % {"tipo": exame.tipo},
        },
    )
    return notificacao


def criar_notificacao_resultado_disponivel(exame):
    if exame.status != Exame.Status.RESULTADO_DISPONIVEL:
        raise ValidationError(
            _("A notificação exige um exame com resultado disponível."),
            code="resultado_indisponivel",
        )

    notificacao, criada = Notificacao.objects.get_or_create(
        exame=exame,
        usuario=exame.usuario,
        tipo=Notificacao.TipoEvento.RESULTADO_DISPONIVEL,
        defaults={
            "mensagem": _(
                "O resultado do exame %(tipo)s está disponível. "
                "Consulte o resultado e realize o acompanhamento necessário."
            )
            % {"tipo": exame.tipo},
        },
    )
    return notificacao
