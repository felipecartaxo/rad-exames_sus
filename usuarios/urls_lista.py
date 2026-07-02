from django.urls import path

from .views import (
    ProfissionalUpdateView,
    UsuarioCreateView,
    UsuarioDeactivateView,
    UsuarioListView,
    UsuarioUpdateView,
)


app_name = "usuarios_lista"

urlpatterns = [
    path("", UsuarioListView.as_view(), name="lista"),
    path("novo/", UsuarioCreateView.as_view(), name="criar"),
    path("<int:pk>/editar/", UsuarioUpdateView.as_view(), name="editar"),
    path(
        "<int:pk>/inativar/",
        UsuarioDeactivateView.as_view(),
        name="inativar",
    ),
    path(
        "profissionais/<int:pk>/editar/",
        ProfissionalUpdateView.as_view(),
        name="editar_profissional",
    ),
]
