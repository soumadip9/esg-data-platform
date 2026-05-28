from rest_framework import serializers

from apps.emissions.models import DataSourceType

from .models import IngestionError, IngestionRun


class IngestionRunSerializer(serializers.ModelSerializer):
    source_type_display = serializers.CharField(source="get_source_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    uploaded_by_name = serializers.CharField(source="uploaded_by.username", read_only=True, default=None)

    class Meta:
        model = IngestionRun
        fields = (
            "id",
            "source_type",
            "source_type_display",
            "filename",
            "status",
            "status_display",
            "uploaded_by",
            "uploaded_by_name",
            "rows_total",
            "rows_success",
            "rows_failed",
            "rows_flagged",
            "rows_duplicate",
            "error_summary",
            "started_at",
            "completed_at",
            "created_at",
        )
        read_only_fields = fields


class IngestionErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionError
        fields = ("id", "row_number", "error_code", "error_message", "raw_row", "created_at")


class FileUploadSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(choices=DataSourceType.choices)
    file = serializers.FileField()

    def validate_file(self, value):
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File exceeds 10MB limit")
        return value
