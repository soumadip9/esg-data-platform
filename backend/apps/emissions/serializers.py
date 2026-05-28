from rest_framework import serializers

from .models import ActivityRecord, AuditLog


class ActivityRecordSerializer(serializers.ModelSerializer):
    reviewed_by_name = serializers.CharField(source="reviewed_by.username", read_only=True, default=None)
    source_type_display = serializers.CharField(source="get_source_type_display", read_only=True)
    scope_display = serializers.CharField(source="get_scope_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ActivityRecord
        fields = (
            "id",
            "source_type",
            "source_type_display",
            "source_reference",
            "scope",
            "scope_display",
            "category",
            "category_display",
            "activity_date",
            "period_start",
            "period_end",
            "description",
            "site_code",
            "site_name",
            "quantity",
            "unit",
            "original_quantity",
            "original_unit",
            "emission_factor_ref",
            "estimated_co2e_kg",
            "status",
            "status_display",
            "flag_reason",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "analyst_notes",
            "is_edited",
            "ingestion_run",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "source_type",
            "source_reference",
            "scope",
            "category",
            "ingestion_run",
            "source_row_hash",
            "is_edited",
            "created_at",
            "updated_at",
            "reviewed_by",
            "reviewed_at",
        )


class ActivityRecordUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityRecord
        fields = ("quantity", "unit", "description", "analyst_notes", "site_name")


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.username", read_only=True, default="System")

    class Meta:
        model = AuditLog
        fields = ("id", "action", "actor", "actor_name", "details", "created_at")
