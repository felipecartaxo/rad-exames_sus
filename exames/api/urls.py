from django.urls import path

from .views import ExameDetailApiView, ExameListApiView


app_name = "api_exames"

urlpatterns = [
    path("", ExameListApiView.as_view(), name="lista"),
    path("<int:pk>/", ExameDetailApiView.as_view(), name="detalhe"),
]
