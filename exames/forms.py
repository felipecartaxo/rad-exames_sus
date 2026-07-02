from django import forms
from django.utils.translation import gettext_lazy as _

from rede_saude.models import Profissional, UnidadeSaude
from usuarios.models import Usuario

from .models import Exame
from .services import TRANSICOES_STATUS
from .validators import validar_documento_resultado


class CriacaoAgendamentoExameForm(forms.Form):
    usuario = forms.ModelChoiceField(
        label=_("Cidadão"),
        queryset=Usuario.objects.none(),
    )
    unidade = forms.ModelChoiceField(
        label=_("Unidade de saúde"),
        queryset=UnidadeSaude.objects.none(),
    )
    profissional = forms.ModelChoiceField(
        label=_("Profissional responsável"),
        queryset=Profissional.objects.none(),
    )
    tipo = forms.CharField(label=_("Tipo do exame"), max_length=150)
    data_agendamento = forms.DateTimeField(
        label=_("Data e horário do agendamento"),
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    data_exame = forms.DateTimeField(
        label=_("Data e horário do exame"),
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["usuario"].queryset = Usuario.objects.filter(
            tipo=Usuario.Tipo.CIDADAO,
            is_active=True,
        ).order_by("nome", "pk")
        self.fields["unidade"].queryset = UnidadeSaude.objects.filter(
            ativo=True
        ).order_by("nome", "pk")
        self.fields["profissional"].queryset = (
            Profissional.objects.filter(is_active=True)
            .select_related("unidade")
            .order_by("nome", "pk")
        )

    def clean(self):
        dados = super().clean()
        data_agendamento = dados.get("data_agendamento")
        data_exame = dados.get("data_exame")
        if (
            data_agendamento
            and data_exame
            and data_exame <= data_agendamento
        ):
            self.add_error(
                "data_exame",
                _("A data do exame deve ser posterior à data do agendamento."),
            )
        return dados


class TransicaoExameForm(forms.Form):
    novo_status = forms.ChoiceField(label=_("Próximo estado"))
    resultado = forms.CharField(
        label=_("Resultado"),
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
    )
    documento_resultado = forms.FileField(
        label=_("Documento do resultado (PDF)"),
        validators=[validar_documento_resultado],
        required=False,
        help_text=_("Arquivo PDF opcional de até 10 MB."),
    )

    def __init__(self, exame, *args, **kwargs):
        self.exame = exame
        super().__init__(*args, **kwargs)
        permitidos = TRANSICOES_STATUS.get(exame.status, set())
        self.fields["novo_status"].choices = [
            (status, Exame.Status(status).label) for status in permitidos
        ]

    def clean(self):
        dados = super().clean()
        novo_status = dados.get("novo_status")
        resultado = (dados.get("resultado") or "").strip()
        documento = dados.get("documento_resultado")

        if novo_status == Exame.Status.RESULTADO_DISPONIVEL:
            if not resultado:
                self.add_error(
                    "resultado",
                    _("Informe o resultado antes de disponibilizá-lo."),
                )
            dados["resultado"] = resultado
        elif resultado or documento:
            raise forms.ValidationError(
                _("Resultado e documento só podem ser enviados ao disponibilizar o resultado.")
            )
        return dados


class FiltroExameCidadaoForm(forms.Form):
    status = forms.ChoiceField(
        label=_("Status do exame"),
        required=False,
        choices=(("", _("Todos os status")), *Exame.Status.choices),
    )
    data_inicio = forms.DateTimeField(
        label=_("Data e horário inicial"),
        required=False,
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    data_fim = forms.DateTimeField(
        label=_("Data e horário final"),
        required=False,
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
    )
    unidade = forms.ModelChoiceField(
        label=_("Unidade de saúde"),
        required=False,
        empty_label=_("Todas as unidades"),
        queryset=UnidadeSaude.objects.none(),
    )

    def __init__(self, usuario, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidade"].queryset = UnidadeSaude.objects.filter(
            exames__usuario=usuario
        ).distinct().order_by("nome", "pk")

    def clean(self):
        dados = super().clean()
        inicio = dados.get("data_inicio")
        fim = dados.get("data_fim")
        if inicio and fim and fim < inicio:
            self.add_error(
                "data_fim",
                _("A data final deve ser igual ou posterior à data inicial."),
            )
        return dados
