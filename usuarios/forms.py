from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
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


class CriacaoUsuarioServidorForm(CadastroCidadaoForm):
    tipo = forms.ChoiceField(
        label=_("Perfil"),
        choices=(
            (Usuario.Tipo.CIDADAO, Usuario.Tipo.CIDADAO.label),
            (Usuario.Tipo.SERVIDOR, Usuario.Tipo.SERVIDOR.label),
        ),
    )

    class Meta(CadastroCidadaoForm.Meta):
        fields = ("nome", "cpf", "tipo")

    def save(self, commit=True):
        usuario = UserCreationForm.save(self, commit=False)
        usuario.tipo = self.cleaned_data["tipo"]
        if commit:
            usuario.save()
        return usuario


class FiltroUsuarioForm(forms.Form):
    busca = forms.CharField(
        label=_("Nome ou CPF"),
        required=False,
        max_length=150,
        widget=forms.TextInput(
            attrs={"placeholder": _("Digite um nome ou CPF")}
        ),
    )
    tipo = forms.ChoiceField(
        label=_("Perfil"),
        required=False,
        choices=(
            ("", _("Todos os perfis")),
            (Usuario.Tipo.CIDADAO, Usuario.Tipo.CIDADAO.label),
            (Usuario.Tipo.SERVIDOR, Usuario.Tipo.SERVIDOR.label),
            (Usuario.Tipo.PROFISSIONAL, Usuario.Tipo.PROFISSIONAL.label),
        ),
    )
    situacao = forms.ChoiceField(
        label=_("Situação"),
        required=False,
        choices=(
            ("", _("Todas as situações")),
            ("ativo", _("Ativo")),
            ("inativo", _("Inativo")),
        ),
    )


class EdicaoUsuarioServidorForm(forms.ModelForm):
    cpf = forms.CharField(
        label=_("CPF"),
        max_length=14,
        widget=forms.TextInput(
            attrs={"autocomplete": "username", "inputmode": "numeric"}
        ),
    )
    password1 = forms.CharField(
        label=_("Nova senha"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=_("Deixe em branco para manter a senha atual."),
    )
    password2 = forms.CharField(
        label=_("Confirmação da nova senha"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ("nome", "cpf", "tipo")
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "name"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].choices = (
            (Usuario.Tipo.CIDADAO, Usuario.Tipo.CIDADAO.label),
            (Usuario.Tipo.SERVIDOR, Usuario.Tipo.SERVIDOR.label),
        )

    def clean_cpf(self):
        cpf = normalizar_cpf(self.cleaned_data["cpf"])
        validar_cpf(cpf)
        if Usuario.objects.exclude(pk=self.instance.pk).filter(cpf=cpf).exists():
            raise forms.ValidationError(
                _("Já existe uma conta cadastrada com este CPF."),
                code="cpf_duplicado",
            )
        return cpf

    def clean(self):
        dados = super().clean()
        senha = dados.get("password1")
        confirmacao = dados.get("password2")
        if senha != confirmacao:
            self.add_error("password2", _("As senhas não coincidem."))
        if senha:
            validate_password(senha, self.instance)
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        senha = self.cleaned_data.get("password1")
        if senha:
            usuario.set_password(senha)
        if commit:
            usuario.save()
        return usuario


class EdicaoProprioPerfilForm(forms.ModelForm):
    cpf = forms.CharField(
        label=_("CPF"),
        max_length=14,
        widget=forms.TextInput(
            attrs={"autocomplete": "username", "inputmode": "numeric"}
        ),
    )
    password1 = forms.CharField(
        label=_("Nova senha"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=_("Deixe em branco para manter a senha atual."),
    )
    password2 = forms.CharField(
        label=_("Confirmação da nova senha"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = Usuario
        fields = ("nome", "cpf")
        widgets = {
            "nome": forms.TextInput(attrs={"autocomplete": "name"}),
        }

    def clean_cpf(self):
        cpf = normalizar_cpf(self.cleaned_data["cpf"])
        validar_cpf(cpf)
        if Usuario.objects.exclude(pk=self.instance.pk).filter(cpf=cpf).exists():
            raise forms.ValidationError(
                _("Já existe uma conta cadastrada com este CPF."),
                code="cpf_duplicado",
            )
        return cpf

    def clean(self):
        dados = super().clean()
        senha = dados.get("password1")
        confirmacao = dados.get("password2")
        if senha != confirmacao:
            self.add_error("password2", _("As senhas não coincidem."))
        if senha:
            validate_password(senha, self.instance)
        return dados

    def save(self, commit=True):
        usuario = super().save(commit=False)
        senha = self.cleaned_data.get("password1")
        if senha:
            usuario.set_password(senha)
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
