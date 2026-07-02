from django.urls import path

from .views import UsuarioCreateView, UsuarioListView, UsuarioUpdateView


app_name = "usuarios_lista"

urlpatterns = [
    path("", UsuarioListView.as_view(), name="lista"),
    path("novo/", UsuarioCreateView.as_view(), name="criar"),
    path("<int:pk>/editar/", UsuarioUpdateView.as_view(), name="editar"),
]
