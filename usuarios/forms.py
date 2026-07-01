from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _

from .managers import normalizar_cpf
from .models import Usuario
from .validators import validar_cpf


class CadastroCidadaoForm(UserCreationForm):
    cpf = forms.CharField(
        label=_("CPF"),
        max_length=14,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "inputmode": "numeric",
                "autofocus": True,
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("nome", "cpf")
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "name"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["password2"].widget.attrs["autocomplete"] = "new-password"

    def clean_cpf(self):
        cpf = normalizar_cpf(self.cleaned_data["cpf"])
        validar_cpf(cpf)
        if Usuario.objects.filter(cpf=cpf).exists():
            raise forms.ValidationError(
                _("Já existe uma conta cadastrada com este CPF."),
                code="cpf_duplicado",
            )
        return cpf

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.tipo = Usuario.Tipo.CIDADAO
        if commit:
            usuario.save()
        return usuario


class LoginCpfForm(AuthenticationForm):
    username = forms.CharField(
        label=_("CPF"),
        max_length=14,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "inputmode": "numeric",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label=_("Senha"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {
        "invalid_login": _("CPF ou senha inválidos."),
        "inactive": _("CPF ou senha inválidos."),
    }

    def clean_username(self):
        return normalizar_cpf(self.cleaned_data["username"])
