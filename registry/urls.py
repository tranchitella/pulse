from django.urls import include, path
from rest_framework import routers

from .views import DeviceViewSet

router = routers.DefaultRouter()
router.register(r"devices", DeviceViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
