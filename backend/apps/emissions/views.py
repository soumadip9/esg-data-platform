from rest_framework import generics, permissions

from apps.tenants.middleware import get_current_tenant

from .models import ActivityRecord, AuditLog
from .serializers import ActivityRecordSerializer, AuditLogSerializer


class TenantQuerysetMixin:
    def get_queryset(self):
        tenant = get_current_tenant() or self.request.user.tenant
        return self.queryset.filter(tenant=tenant)


class ActivityListView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = ActivityRecordSerializer
    queryset = ActivityRecord.objects.select_related("reviewed_by", "ingestion_run")
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "source_type", "scope", "category"]
    search_fields = ["description", "source_reference", "site_code", "site_name"]
    ordering_fields = ["activity_date", "created_at", "quantity", "status"]


class ActivityDetailView(TenantQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = ActivityRecordSerializer
    queryset = ActivityRecord.objects.select_related("reviewed_by", "ingestion_run")
    permission_classes = [permissions.IsAuthenticated]


class ActivityAuditLogView(TenantQuerysetMixin, generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant() or self.request.user.tenant
        activity_id = self.kwargs["pk"]
        return AuditLog.objects.filter(tenant=tenant, activity_id=activity_id).select_related("actor")
