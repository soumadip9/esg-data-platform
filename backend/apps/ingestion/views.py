from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tenants.middleware import get_current_tenant

from .models import IngestionError, IngestionRun
from .serializers import FileUploadSerializer, IngestionErrorSerializer, IngestionRunSerializer
from .services.pipeline import run_ingestion
from .tasks import process_ingestion_task


class IngestionUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = get_current_tenant() or request.user.tenant
        if not tenant:
            return Response({"detail": "User has no tenant assigned"}, status=status.HTTP_403_FORBIDDEN)

        uploaded_file = serializer.validated_data["file"]
        content = uploaded_file.read().decode("utf-8-sig", errors="replace")

        run = IngestionRun.objects.create(
            tenant=tenant,
            source_type=serializer.validated_data["source_type"],
            filename=uploaded_file.name,
            uploaded_by=request.user,
        )

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            run_ingestion(run, content)
        else:
            process_ingestion_task.delay(str(run.id), content)

        return Response(IngestionRunSerializer(run).data, status=status.HTTP_202_ACCEPTED)


class IngestionRunListView(generics.ListAPIView):
    serializer_class = IngestionRunSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["source_type", "status"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        tenant = get_current_tenant() or self.request.user.tenant
        return IngestionRun.objects.filter(tenant=tenant).select_related("uploaded_by")


class IngestionRunDetailView(generics.RetrieveAPIView):
    serializer_class = IngestionRunSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant() or self.request.user.tenant
        return IngestionRun.objects.filter(tenant=tenant).select_related("uploaded_by")


class IngestionErrorListView(generics.ListAPIView):
    serializer_class = IngestionErrorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant() or self.request.user.tenant
        run_id = self.kwargs["run_id"]
        return IngestionError.objects.filter(run_id=run_id, run__tenant=tenant)
