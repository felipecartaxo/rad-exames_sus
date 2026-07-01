from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from exames.models import Exame

from .models import Notificacao


def criar_notificacao_resultado_disponivel(exame):
    if exame.status != Exame.Status.RESULTADO_DISPONIVEL:
        raise ValidationError(
            _("A notificação exige um exame com resultado disponível."),
            code="resultado_indisponivel",
        )

    notificacao, criada = Notificacao.objects.get_or_create(
        exame=exame,
        defaults={
            "usuario": exame.usuario,
            "mensagem": _(
                "O resultado do exame %(tipo)s está disponível. "
                "Consulte o resultado e realize o acompanhamento necessário."
            )
            % {"tipo": exame.tipo},
        },
    )
    return notificacao
