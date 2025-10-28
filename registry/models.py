import uuid

from auditlog.registry import auditlog
from django.db import models


@auditlog.register()
class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
