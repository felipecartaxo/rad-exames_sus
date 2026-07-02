from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import Profissional, UnidadeSaude
from .validators import normalizar_cpf, validar_cpf


class ProfissionalAdminForm(forms.ModelForm):
    cpf = forms.CharField(label=_("CPF"), max_length=14)
    password1 = forms.CharField(
        label=_("Senha"),
        widget=forms.PasswordInput,
        required=False,
    )
    password2 = forms.CharField(
        label=_("Confirmação da senha"),
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model = Profissional
        fields = (
            "cpf",
            "nome",
            "cargo",
            "especialidade",
            "unidade",
            "is_active",
        )

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

    def clean(self):
        dados = super().clean()
        senha = dados.get("password1")
        confirmacao = dados.get("password2")

        if not self.instance.pk and not senha:
            self.add_error("password1", _("A senha é obrigatória."))
        if senha != confirmacao:
            self.add_error("password2", _("As senhas não coincidem."))
        if senha:
            validate_password(senha, self.instance)
        return dados

    def save(self, commit=True):
        profissional = super().save(commit=False)
        senha = self.cleaned_data.get("password1")
        if senha:
            profissional.set_password(senha)
        if commit:
            profissional.save()
            self.save_m2m()
        return profissional


class EdicaoProfissionalServidorForm(ProfissionalAdminForm):
    class Meta(ProfissionalAdminForm.Meta):
        fields = (
            "cpf",
            "nome",
            "cargo",
            "especialidade",
            "unidade",
        )
