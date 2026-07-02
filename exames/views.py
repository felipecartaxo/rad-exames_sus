from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from usuarios.permissions import ServidorAutorizadoMixin

from .forms import (
    CriacaoAgendamentoExameForm,
    FiltroExameCidadaoForm,
    TransicaoExameForm,
)
from .models import Exame
from .permissions import CidadaoAutenticadoMixin, ProfissionalAutorizadoMixin
from .services import (
    TRANSICOES_STATUS,
    criar_agendamento_exame,
    excluir_exame_atribuido,
    transicionar_status,
)


class CriacaoAgendamentoExameView(ServidorAutorizadoMixin, FormView):
    template_name = "exames/criar.html"
    form_class = CriacaoAgendamentoExameForm
    success_url = reverse_lazy("exames:criar")
    permission_required = ("exames.add_agendamento", "exames.add_exame")

    def form_valid(self, form):
        criar_agendamento_exame(**form.cleaned_data)
        messages.success(
            self.request,
            _("Agendamento e exame criados com sucesso."),
        )
        return super().form_valid(form)


class ExameListView(CidadaoAutenticadoMixin, ListView):
    model = Exame
    template_name = "exames/lista.html"
    context_object_name = "exames"
    paginate_by = 5

    def get_form_filtros(self):
        if not hasattr(self, "form_filtros"):
            self.form_filtros = FiltroExameCidadaoForm(
                self.request.user,
                self.request.GET or None,
            )
        return self.form_filtros

    def get_queryset(self):
        queryset = (
            Exame.objects.filter(usuario=self.request.user)
            .select_related("unidade")
        )
        formulario = self.get_form_filtros()
        if formulario.is_valid():
            filtros = formulario.cleaned_data
            if filtros["status"]:
                queryset = queryset.filter(status=filtros["status"])
            if filtros["data_inicio"]:
                queryset = queryset.filter(data__gte=filtros["data_inicio"])
            if filtros["data_fim"]:
                queryset = queryset.filter(data__lte=filtros["data_fim"])
            if filtros["unidade"]:
                queryset = queryset.filter(unidade=filtros["unidade"])
        return queryset.order_by("-data", "-pk")

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        contexto["form_filtros"] = self.get_form_filtros()
        return contexto


class ExameProfissionalListView(ProfissionalAutorizadoMixin, ListView):
    model = Exame
    template_name = "exames/lista_profissional.html"
    context_object_name = "exames"
    paginate_by = 5

    def get_queryset(self):
        return (
            Exame.objects.filter(profissional_id=self.request.user.pk)
            .select_related("usuario", "unidade")
            .order_by("-data", "-pk")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto


class ExameProfissionalDetailView(ProfissionalAutorizadoMixin, FormView):
    template_name = "exames/detalhe_profissional.html"
    form_class = TransicaoExameForm
    permission_required = "exames.change_exame"

    def get_exame(self):
        if not hasattr(self, "exame"):
            self.exame = get_object_or_404(
                Exame.objects.select_related(
                    "usuario",
                    "unidade",
                    "profissional",
                    "agendamento",
                ),
                pk=self.kwargs["pk"],
                profissional_id=self.request.user.pk,
            )
        return self.exame

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["exame"] = self.get_exame()
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        exame = self.get_exame()
        contexto["exame"] = exame
        contexto["possui_transicoes"] = bool(
            TRANSICOES_STATUS.get(exame.status)
        )
        return contexto

    def form_valid(self, form):
        exame = self.get_exame()
        try:
            transicionar_status(
                exame,
                form.cleaned_data["novo_status"],
                resultado=form.cleaned_data.get("resultado"),
                documento_resultado=form.cleaned_data.get(
                    "documento_resultado"
                ),
            )
        except ValidationError as erro:
            if hasattr(erro, "message_dict"):
                for campo, mensagens_erro in erro.message_dict.items():
                    form.add_error(
                        campo if campo in form.fields else None,
                        mensagens_erro,
                    )
            else:
                form.add_error(None, erro.messages)
            return self.form_invalid(form)

        messages.success(self.request, _("Estado do exame atualizado com sucesso."))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "exames:detalhe_profissional",
            kwargs={"pk": self.kwargs["pk"]},
        )


class ExameProfissionalDeleteView(
    ProfissionalAutorizadoMixin,
    TemplateView,
):
    template_name = "exames/confirmar_exclusao_profissional.html"
    permission_required = "exames.view_exame"

    def get_exame(self):
        if not hasattr(self, "exame"):
            self.exame = get_object_or_404(
                Exame.objects.select_related(
                    "usuario",
                    "unidade",
                    "profissional",
                    "agendamento",
                ),
                pk=self.kwargs["pk"],
                profissional_id=self.request.user.pk,
            )
        return self.exame

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["exame"] = self.get_exame()
        return contexto

    def post(self, request, *args, **kwargs):
        exame = self.get_exame()
        tipo = exame.tipo
        excluir_exame_atribuido(exame)
        messages.success(
            request,
            _("O exame %(tipo)s e seus dados vinculados foram excluídos.")
            % {"tipo": tipo},
        )
        return redirect("exames:lista_profissional")


@login_required(login_url="usuarios:login")
def baixar_documento_resultado(request, pk):
    exame = get_object_or_404(Exame.objects.select_related("profissional"), pk=pk)
    pode_acessar = (
        request.user.tipo == request.user.Tipo.CIDADAO
        and exame.usuario_id == request.user.pk
    ) or (
        request.user.tipo == request.user.Tipo.PROFISSIONAL
        and exame.profissional_id == request.user.pk
        and request.user.has_perm("exames.view_exame")
    )
    if not pode_acessar:
        raise PermissionDenied(_("Você não pode acessar este documento."))
    if not exame.documento_resultado:
        raise Http404
    try:
        arquivo = exame.documento_resultado.open("rb")
    except FileNotFoundError as erro:
        raise Http404 from erro
    return FileResponse(
        arquivo,
        as_attachment=True,
        filename=exame.documento_resultado.name.rsplit("/", 1)[-1],
        content_type="application/pdf",
    )


class ExameHistoricoView(CidadaoAutenticadoMixin, ListView):
    model = Exame
    template_name = "exames/historico.html"
    context_object_name = "exames"
    paginate_by = 5

    def get_queryset(self):
        return (
            Exame.objects.filter(usuario=self.request.user)
            .select_related("unidade", "profissional")
            .order_by("-data", "-pk")
        )

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["querystring"] = parametros.urlencode()
        return contexto
