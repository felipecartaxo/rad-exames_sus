from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views import View
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from rede_saude.forms import EdicaoProfissionalServidorForm
from rede_saude.models import Profissional

from .forms import (
    CadastroCidadaoForm,
    CriacaoUsuarioServidorForm,
    EdicaoUsuarioServidorForm,
    EdicaoProprioPerfilForm,
    FiltroUsuarioForm,
    LoginCpfForm,
)
from .models import Usuario
from .permissions import ServidorMixin


class CadastroCidadaoView(FormView):
    template_name = "usuarios/cadastro.html"
    form_class = CadastroCidadaoForm
    success_url = reverse_lazy("usuarios:login")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            _("Cadastro realizado com sucesso."),
        )
        return super().form_valid(form)


class LoginCpfView(LoginView):
    template_name = "usuarios/login.html"
    authentication_form = LoginCpfForm
    redirect_authenticated_user = True

    def get_success_url(self):
        redirect_url = self.get_redirect_url()
        if redirect_url:
            return redirect_url
        if self.request.user.is_superuser:
            return reverse("admin:index")
        if self.request.user.tipo == Usuario.Tipo.CIDADAO:
            return reverse("exames:lista")
        if self.request.user.tipo == Usuario.Tipo.PROFISSIONAL:
            return reverse("exames:lista_profissional")
        if self.request.user.tipo == Usuario.Tipo.SERVIDOR:
            return reverse("usuarios_lista:lista")
        return reverse("usuarios:inicio")


class ContaView(LoginRequiredMixin, FormView):
    template_name = "usuarios/conta.html"
    form_class = EdicaoProprioPerfilForm
    success_url = reverse_lazy("usuarios:inicio")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        usuario = form.save()
        update_session_auth_hash(self.request, usuario)
        messages.success(self.request, _("Seus dados foram atualizados."))
        return super().form_valid(form)


class LogoutCpfView(LogoutView):
    next_page = reverse_lazy("usuarios:login")


class UsuarioListView(ServidorMixin, ListView):
    model = Usuario
    template_name = "usuarios/lista.html"
    context_object_name = "usuarios"
    paginate_by = 5

    def get_form_filtros(self):
        if not hasattr(self, "form_filtros"):
            self.form_filtros = FiltroUsuarioForm(self.request.GET or None)
        return self.form_filtros

    def get_queryset(self):
        queryset = Usuario.objects.select_related("profissional")
        formulario = self.get_form_filtros()
        if formulario.is_valid():
            filtros = formulario.cleaned_data
            if filtros["busca"]:
                busca = filtros["busca"].strip()
                cpf = "".join(
                    caractere for caractere in busca if caractere.isdigit()
                )
                consulta = Q(nome__icontains=busca)
                if cpf:
                    consulta |= Q(cpf__icontains=cpf)
                queryset = queryset.filter(consulta)
            if filtros["tipo"]:
                queryset = queryset.filter(tipo=filtros["tipo"])
            if filtros["situacao"]:
                queryset = queryset.filter(
                    is_active=filtros["situacao"] == "ativo"
                )
        return queryset.order_by("nome", "cpf", "pk")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        contexto["form_filtros"] = self.get_form_filtros()
        return contexto


class UsuarioCreateView(ServidorMixin, FormView):
    template_name = "usuarios/criar.html"
    form_class = CriacaoUsuarioServidorForm
    success_url = reverse_lazy("usuarios_lista:lista")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Usuário criado com sucesso."))
        return super().form_valid(form)


class UsuarioUpdateView(ServidorMixin, FormView):
    template_name = "usuarios/editar.html"
    form_class = EdicaoUsuarioServidorForm
    success_url = reverse_lazy("usuarios_lista:lista")

    def get_usuario(self):
        if not hasattr(self, "usuario_editado"):
            self.usuario_editado = get_object_or_404(
                Usuario.objects.filter(is_superuser=False).exclude(
                    tipo=Usuario.Tipo.PROFISSIONAL
                ),
                pk=self.kwargs["pk"],
            )
        return self.usuario_editado

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_usuario()
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["usuario_editado"] = self.get_usuario()
        return contexto

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Usuário atualizado com sucesso."))
        return super().form_valid(form)


class UsuarioDeactivateView(ServidorMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        usuario = get_object_or_404(
            Usuario,
            pk=self.kwargs["pk"],
            tipo__in=(Usuario.Tipo.CIDADAO, Usuario.Tipo.PROFISSIONAL),
            is_active=True,
            is_superuser=False,
        )
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        messages.success(
            request,
            _("O perfil de %(nome)s foi inativado.") % {"nome": usuario.nome},
        )
        return redirect("usuarios_lista:lista")


class UsuarioActivateView(ServidorMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        usuario = get_object_or_404(
            Usuario,
            pk=self.kwargs["pk"],
            tipo__in=(Usuario.Tipo.CIDADAO, Usuario.Tipo.PROFISSIONAL),
            is_active=False,
            is_superuser=False,
        )
        usuario.is_active = True
        usuario.save(update_fields=["is_active"])
        messages.success(
            request,
            _("O perfil de %(nome)s foi reativado.") % {"nome": usuario.nome},
        )
        return redirect("usuarios_lista:lista")


class UsuarioBulkStatusView(ServidorMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        acao = request.POST.get("acao")
        identificadores = request.POST.getlist("usuarios")
        if acao not in {"inativar", "reativar"} or not identificadores:
            messages.warning(
                request,
                _("Selecione ao menos um perfil e uma ação válida."),
            )
            return redirect("usuarios_lista:lista")

        ativos = acao == "reativar"
        quantidade = Usuario.objects.filter(
            pk__in=identificadores,
            tipo__in=(Usuario.Tipo.CIDADAO, Usuario.Tipo.PROFISSIONAL),
            is_superuser=False,
        ).exclude(is_active=ativos).update(is_active=ativos)
        if ativos:
            mensagem = ngettext(
                "%(quantidade)d perfil foi reativado.",
                "%(quantidade)d perfis foram reativados.",
                quantidade,
            ) % {"quantidade": quantidade}
        else:
            mensagem = ngettext(
                "%(quantidade)d perfil foi inativado.",
                "%(quantidade)d perfis foram inativados.",
                quantidade,
            ) % {"quantidade": quantidade}
        messages.success(request, mensagem)
        return redirect("usuarios_lista:lista")


class ProfissionalUpdateView(ServidorMixin, FormView):
    template_name = "usuarios/editar_profissional.html"
    form_class = EdicaoProfissionalServidorForm
    success_url = reverse_lazy("usuarios_lista:lista")

    def get_profissional(self):
        if not hasattr(self, "profissional_editado"):
            self.profissional_editado = get_object_or_404(
                Profissional.objects.select_related("unidade"),
                pk=self.kwargs["pk"],
                is_superuser=False,
            )
        return self.profissional_editado

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_profissional()
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["profissional_editado"] = self.get_profissional()
        return contexto

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            _("Profissional de saúde atualizado com sucesso."),
        )
        return super().form_valid(form)
