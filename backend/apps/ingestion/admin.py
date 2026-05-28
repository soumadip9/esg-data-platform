from django.contrib import admin

from .models import IngestionError, IngestionRun


class IngestionErrorInline(admin.TabularInline):
    model = IngestionError
    extra = 0
    readonly_fields = ("row_number", "error_code", "error_message")


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = ("filename", "source_type", "status", "rows_success", "rows_failed", "tenant", "created_at")
    list_filter = ("source_type", "status", "tenant")
    inlines = [IngestionErrorInline]


@admin.register(IngestionError)
class IngestionErrorAdmin(admin.ModelAdmin):
    list_display = ("run", "row_number", "error_code", "error_message")
