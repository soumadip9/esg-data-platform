import uuid

from django.db import models


class Tenant(models.Model):
    """Organization boundary for multi-tenant data isolation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlantCode(models.Model):
    """Lookup table mapping SAP plant codes to human-readable sites."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="plant_codes")
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = [("tenant", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"
