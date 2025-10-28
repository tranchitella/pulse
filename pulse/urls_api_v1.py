from django.urls import include, path

from registry.urls import urlpatterns as registry_urls

app_name = "api_v1"

urlpatterns = [
    path("registry/", include((registry_urls, "registry"))),
]
