from django.urls import path

from .views import CadastroCidadaoView


app_name = "usuarios"

urlpatterns = [
    path("cadastro/", CadastroCidadaoView.as_view(), name="cadastro"),
]

