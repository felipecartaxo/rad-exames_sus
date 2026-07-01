from django.urls import path

from .views import ExameHistoricoView, ExameListView


app_name = "exames"

urlpatterns = [
    path("", ExameListView.as_view(), name="lista"),
    path("historico/", ExameHistoricoView.as_view(), name="historico"),
]
