from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("usuarios.urls")),
    path("usuarios/", include("usuarios.urls_lista")),
    path("exames/", include("exames.urls")),
]
