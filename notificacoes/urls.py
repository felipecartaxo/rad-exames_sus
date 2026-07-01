from django.urls import path

from .views import MarcarNotificacoesLidasView, NotificacaoListView


app_name = "notificacoes"

urlpatterns = [
    path("", NotificacaoListView.as_view(), name="lista"),
    path("marcar-como-lidas/", MarcarNotificacoesLidasView.as_view(), name="marcar_lidas"),
]

