from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from .models import Usuario


class UsuarioCreationAdminForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ("cpf", "nome", "tipo")

    def clean_tipo(self):
        tipo = self.cleaned_data["tipo"]
        if tipo == Usuario.Tipo.PROFISSIONAL:
            raise forms.ValidationError(
                _("Cadastre profissionais na área de profissionais de saúde.")
            )
        return tipo


class UsuarioChangeAdminForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = "__all__"

    def clean_tipo(self):
        tipo = self.cleaned_data["tipo"]
        if tipo == Usuario.Tipo.PROFISSIONAL:
            raise forms.ValidationError(
                _("Edite profissionais na área de profissionais de saúde.")
            )
        return tipo


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    add_form = UsuarioCreationAdminForm
    form = UsuarioChangeAdminForm
    model = Usuario

    list_display = ("cpf", "nome", "tipo", "is_active", "is_staff")
    list_filter = ("tipo", "is_active", "is_staff", "is_superuser")
    search_fields = ("cpf", "nome")
    ordering = ("cpf",)
    filter_horizontal = ("groups", "user_permissions")
    actions = ("ativar_usuarios", "desativar_usuarios")

    fieldsets = (
        (None, {"fields": ("cpf", "password")}),
        (_("Dados pessoais"), {"fields": ("nome", "tipo")}),
        (
            _("Permissões"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Datas importantes"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("cpf", "nome", "tipo", "password1", "password2"),
            },
        ),
    )
    readonly_fields = ("last_login",)

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(
            tipo=Usuario.Tipo.PROFISSIONAL
        )

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description=_("Ativar usuários selecionados"))
    def ativar_usuarios(self, request, queryset):
        quantidade = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                "%d usuário foi ativado.",
                "%d usuários foram ativados.",
                quantidade,
            )
            % quantidade,
            messages.SUCCESS,
        )

    @admin.action(description=_("Desativar usuários selecionados"))
    def desativar_usuarios(self, request, queryset):
        quantidade = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                "%d usuário foi desativado.",
                "%d usuários foram desativados.",
                quantidade,
            )
            % quantidade,
            messages.SUCCESS,
        )
