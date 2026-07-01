from django.urls import path

from .views import UsuarioListView


app_name = "usuarios_lista"

urlpatterns = [
    path("", UsuarioListView.as_view(), name="lista"),
]
