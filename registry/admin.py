from auditlog.mixins import AuditlogHistoryAdminMixin
from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Device


@admin.register(Device)
class DeviceAdmin(AuditlogHistoryAdminMixin, ModelAdmin):
    list_display = (
        "id",
        "name",
    )
    search_fields = ("id", "name")
    list_filter = ("id", "name")
    show_auditlog_history_link = True
