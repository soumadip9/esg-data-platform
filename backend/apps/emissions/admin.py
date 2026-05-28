from django.contrib import admin

from .models import ActivityRecord, AuditLog


@admin.register(ActivityRecord)
class ActivityRecordAdmin(admin.ModelAdmin):
    list_display = (
        "source_reference",
        "category",
        "scope",
        "quantity",
        "unit",
        "status",
        "activity_date",
        "tenant",
    )
    list_filter = ("tenant", "status", "scope", "source_type", "category")
    search_fields = ("source_reference", "description", "site_code")
    readonly_fields = ("created_at", "updated_at", "source_row_hash")


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "activity", "created_at", "tenant")
    list_filter = ("action", "tenant")
    readonly_fields = ("created_at",)
