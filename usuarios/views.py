from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .forms import CadastroCidadaoForm, LoginCpfForm
from .models import Usuario
from .permissions import ServidorAutorizadoMixin


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
        if (
            self.request.user.tipo == Usuario.Tipo.SERVIDOR
            and self.request.user.has_perm("usuarios.view_usuario")
        ):
            return reverse("usuarios_lista:lista")
        return reverse("usuarios:inicio")


class ContaView(LoginRequiredMixin, TemplateView):
    template_name = "usuarios/conta.html"


class LogoutCpfView(LogoutView):
    next_page = reverse_lazy("usuarios:login")


class UsuarioListView(ServidorAutorizadoMixin, ListView):
    model = Usuario
    template_name = "usuarios/lista.html"
    context_object_name = "usuarios"
    paginate_by = 10
    permission_required = "usuarios.view_usuario"

    def get_queryset(self):
        return Usuario.objects.order_by("nome", "cpf", "pk")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto
