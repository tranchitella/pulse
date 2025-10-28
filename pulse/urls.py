from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

urlpatterns = (
    [
        path("i18n/", include("django.conf.urls.i18n")),
    ]
    + i18n_patterns(
        path("admin/", admin.site.urls),
    )
    + [
        path("api/v1/", include(("pulse.urls_api_v1", "api_v1"), namespace="v1")),
        path(
            "api/v1/schema/",
            SpectacularAPIView.as_view(api_version="v1"),
            name="schema_v1",
        ),
        path(
            "api/v1/schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema_v1"),
            name="redoc_v1",
        ),
    ]
)
