from django.db import models
from django_tenants.models import DomainMixin
from tenant_users.tenants.models import TenantBase, UserProfile


class User(UserProfile):
    pass


class Tenant(TenantBase):
    name = models.CharField(max_length=100)


class Domain(DomainMixin):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
