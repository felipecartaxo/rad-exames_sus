from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import Profissional, UnidadeSaude
from .validators import normalizar_cpf, validar_cpf


class ProfissionalAdminForm(forms.ModelForm):
    cpf = forms.CharField(label=_("CPF"), max_length=14)

    class Meta:
        model = Profissional
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        unidades_disponiveis = Q(ativo=True)
        if self.instance.pk and self.instance.unidade_id:
            unidades_disponiveis |= Q(pk=self.instance.unidade_id)
        self.fields["unidade"].queryset = UnidadeSaude.objects.filter(
            unidades_disponiveis
        )

    def clean_cpf(self):
        cpf = normalizar_cpf(self.cleaned_data["cpf"])
        validar_cpf(cpf)
        return cpf
