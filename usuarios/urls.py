from django.urls import path

from .views import CadastroCidadaoView, ContaView, LoginCpfView, LogoutCpfView


app_name = "usuarios"

urlpatterns = [
    path("", ContaView.as_view(), name="inicio"),
    path("cadastro/", CadastroCidadaoView.as_view(), name="cadastro"),
    path("entrar/", LoginCpfView.as_view(), name="login"),
    path("sair/", LogoutCpfView.as_view(), name="logout"),
]
