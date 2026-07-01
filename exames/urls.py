from django.urls import path

from .views import ExameListView


app_name = "exames"

urlpatterns = [
    path("", ExameListView.as_view(), name="lista"),
]

