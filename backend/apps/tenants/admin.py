from django.contrib import admin

from .models import PlantCode, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(PlantCode)
class PlantCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "tenant", "country")
    list_filter = ("tenant",)
