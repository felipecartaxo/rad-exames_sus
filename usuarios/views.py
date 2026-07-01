from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import CadastroCidadaoForm, LoginCpfForm


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
        return reverse("usuarios:inicio")


class ContaView(LoginRequiredMixin, TemplateView):
    template_name = "usuarios/conta.html"


class LogoutCpfView(LogoutView):
    next_page = reverse_lazy("usuarios:login")
