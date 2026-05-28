import uuid

from django.conf import settings
from django.db import models


class EmissionScope(models.TextChoices):
    SCOPE_1 = "scope_1", "Scope 1 — Direct"
    SCOPE_2 = "scope_2", "Scope 2 — Purchased Energy"
    SCOPE_3 = "scope_3", "Scope 3 — Value Chain"


class ActivityCategory(models.TextChoices):
    FUEL = "fuel", "Stationary/Mobile Fuel"
    PROCUREMENT = "procurement", "Purchased Goods"
    ELECTRICITY = "electricity", "Purchased Electricity"
    TRAVEL_AIR = "travel_air", "Business Travel — Air"
    TRAVEL_HOTEL = "travel_hotel", "Business Travel — Hotel"
    TRAVEL_GROUND = "travel_ground", "Business Travel — Ground"


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "Pending Review"
    FLAGGED = "flagged", "Flagged — Needs Attention"
    APPROVED = "approved", "Approved"
    LOCKED = "locked", "Locked for Audit"


class DataSourceType(models.TextChoices):
    SAP = "sap", "SAP Procurement Export"
    UTILITY = "utility", "Utility Portal CSV"
    TRAVEL = "travel", "Corporate Travel Export"


class ActivityRecord(models.Model):
    """
    Normalized emission activity row after ingestion.
    Single source of truth for analyst review and audit export.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="activities")

    # Source-of-truth tracking
    source_type = models.CharField(max_length=20, choices=DataSourceType.choices)
    ingestion_run = models.ForeignKey(
        "ingestion.IngestionRun",
        on_delete=models.PROTECT,
        related_name="activities",
    )
    source_row_hash = models.CharField(max_length=64, help_text="SHA-256 of raw source row for dedup")
    source_reference = models.CharField(max_length=255, blank=True, help_text="PO number, meter ID, expense ID, etc.")

    # GHG categorization
    scope = models.CharField(max_length=20, choices=EmissionScope.choices)
    category = models.CharField(max_length=30, choices=ActivityCategory.choices)

    # Normalized activity data
    activity_date = models.DateField()
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    site_code = models.CharField(max_length=50, blank=True)
    site_name = models.CharField(max_length=255, blank=True)

    quantity = models.DecimalField(max_digits=18, decimal_places=6)
    unit = models.CharField(max_length=20, help_text="Normalized unit (L, kWh, km, nights, etc.)")
    original_quantity = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    original_unit = models.CharField(max_length=20, blank=True)

    # Optional emission estimate (not computed in prototype — placeholder for downstream calc)
    emission_factor_ref = models.CharField(max_length=100, blank=True)
    estimated_co2e_kg = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    # Review workflow
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    flag_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_activities",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    analyst_notes = models.TextField(blank=True)

    # Edit tracking
    is_edited = models.BooleanField(default=False)
    raw_payload = models.JSONField(default=dict, help_text="Original parsed row for audit replay")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "source_type"]),
            models.Index(fields=["tenant", "scope"]),
            models.Index(fields=["tenant", "activity_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "source_type", "source_row_hash"],
                name="unique_activity_per_source_row",
            ),
        ]

    def __str__(self):
        return f"{self.category} — {self.quantity} {self.unit} ({self.activity_date})"


class AuditLog(models.Model):
    """Immutable audit trail for all state changes on activity records."""

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        FLAGGED = "flagged", "Flagged"
        APPROVED = "approved", "Approved"
        LOCKED = "locked", "Locked"
        EDITED = "edited", "Edited by Analyst"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="audit_logs")
    activity = models.ForeignKey(
        ActivityRecord,
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    ingestion_run = models.ForeignKey(
        "ingestion.IngestionRun",
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} @ {self.created_at}"
