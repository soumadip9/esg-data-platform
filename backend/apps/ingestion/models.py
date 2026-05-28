import uuid

from django.conf import settings
from django.db import models

from apps.emissions.models import DataSourceType


class IngestionRun(models.Model):
    """Tracks each file upload or API pull ingestion attempt."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial Success"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="ingestion_runs")
    source_type = models.CharField(max_length=20, choices=DataSourceType.choices)
    filename = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploads",
    )

    rows_total = models.PositiveIntegerField(default=0)
    rows_success = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    rows_flagged = models.PositiveIntegerField(default=0)
    rows_duplicate = models.PositiveIntegerField(default=0)

    error_summary = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_type} — {self.filename} ({self.status})"


class IngestionError(models.Model):
    """Row-level ingestion failures for analyst visibility."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(IngestionRun, on_delete=models.CASCADE, related_name="errors")
    row_number = models.PositiveIntegerField()
    raw_row = models.TextField(blank=True)
    error_code = models.CharField(max_length=50)
    error_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["row_number"]
