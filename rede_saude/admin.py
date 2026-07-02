from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from .forms import ProfissionalAdminForm
from .models import Profissional, UnidadeSaude


class SemExclusaoFisicaAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UnidadeSaude)
class UnidadeSaudeAdmin(SemExclusaoFisicaAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "endereco", "contato", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "endereco", "contato")
    ordering = ("nome",)
    actions = ("ativar_unidades", "desativar_unidades")

    @admin.action(description=_("Ativar unidades selecionadas"))
    def ativar_unidades(self, request, queryset):
        quantidade = queryset.update(ativo=True)
        self.message_user(
            request,
            ngettext(
                "%d unidade foi ativada.",
                "%d unidades foram ativadas.",
                quantidade,
            )
            % quantidade,
            messages.SUCCESS,
        )

    @admin.action(description=_("Desativar unidades selecionadas"))
    def desativar_unidades(self, request, queryset):
        if request.POST.get("confirmar"):
            quantidade = queryset.update(ativo=False)
            self.message_user(
                request,
                ngettext(
                    "%d unidade foi desativada.",
                    "%d unidades foram desativadas.",
                    quantidade,
                )
                % quantidade,
                messages.SUCCESS,
            )
            return None

        contexto = {
            **self.admin_site.each_context(request),
            "title": _("Confirmar desativação de unidades"),
            "opts": self.model._meta,
            "objetos": queryset,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "action_name": "desativar_unidades",
        }
        return TemplateResponse(
            request,
            "admin/confirmar_desativacao_unidades.html",
            contexto,
        )


@admin.register(Profissional)
class ProfissionalAdmin(SemExclusaoFisicaAdminMixin, admin.ModelAdmin):
    form = ProfissionalAdminForm
    list_display = (
        "nome",
        "cpf",
        "cargo",
        "especialidade",
        "unidade",
        "is_active",
    )
    list_filter = ("is_active", "cargo", "unidade")
    search_fields = ("nome", "cpf", "cargo", "especialidade", "unidade__nome")
    ordering = ("nome",)
    list_select_related = ("unidade",)
    actions = ("ativar_profissionais", "desativar_profissionais")

    def has_add_permission(self, request):
        return request.user.is_superuser

    @admin.action(description=_("Ativar profissionais selecionados"))
    def ativar_profissionais(self, request, queryset):
        quantidade = queryset.update(is_active=True)
        self.message_user(
            request,
            ngettext(
                "%d profissional foi ativado.",
                "%d profissionais foram ativados.",
                quantidade,
            )
            % quantidade,
            messages.SUCCESS,
        )

    @admin.action(description=_("Desativar profissionais selecionados"))
    def desativar_profissionais(self, request, queryset):
        quantidade = queryset.update(is_active=False)
        self.message_user(
            request,
            ngettext(
                "%d profissional foi desativado.",
                "%d profissionais foram desativados.",
                quantidade,
            )
            % quantidade,
            messages.SUCCESS,
        )
