from django.urls import path

from .views import (
    CriacaoAgendamentoExameView,
    ExameProfissionalDetailView,
    ExameProfissionalDeleteView,
    ExameHistoricoView,
    ExameListView,
    ExameProfissionalListView,
    baixar_documento_resultado,
)


app_name = "exames"

urlpatterns = [
    path("", ExameListView.as_view(), name="lista"),
    path("novo/", CriacaoAgendamentoExameView.as_view(), name="criar"),
    path(
        "profissional/",
        ExameProfissionalListView.as_view(),
        name="lista_profissional",
    ),
    path(
        "profissional/<int:pk>/",
        ExameProfissionalDetailView.as_view(),
        name="detalhe_profissional",
    ),
    path(
        "profissional/<int:pk>/excluir/",
        ExameProfissionalDeleteView.as_view(),
        name="excluir_profissional",
    ),
    path(
        "<int:pk>/documento/",
        baixar_documento_resultado,
        name="documento_resultado",
    ),
    path("historico/", ExameHistoricoView.as_view(), name="historico"),
]
