from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .forms import (
    CadastroCidadaoForm,
    CriacaoUsuarioServidorForm,
    EdicaoUsuarioServidorForm,
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


class ContaView(LoginRequiredMixin, TemplateView):
    template_name = "usuarios/conta.html"


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
        queryset = Usuario.objects.exclude(
            tipo=Usuario.Tipo.PROFISSIONAL
        )
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
