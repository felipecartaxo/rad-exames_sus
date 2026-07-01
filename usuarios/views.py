from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from .forms import CadastroCidadaoForm


class CadastroCidadaoView(FormView):
    template_name = "usuarios/cadastro.html"
    form_class = CadastroCidadaoForm
    success_url = reverse_lazy("usuarios:cadastro")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            _("Cadastro realizado com sucesso."),
        )
        return super().form_valid(form)

