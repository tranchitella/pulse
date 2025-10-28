from rest_framework import permissions, viewsets
from rest_framework_api_key.permissions import HasAPIKey

from .models import Device
from .serializers import DeviceSerializer

permission_classes = [HasAPIKey | permissions.IsAuthenticated]


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by("id")
    serializer_class = DeviceSerializer
    permission_classes = permission_classes
