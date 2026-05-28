from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.emissions.models import ActivityRecord, AuditLog, ReviewStatus
from apps.emissions.serializers import ActivityRecordSerializer, ActivityRecordUpdateSerializer
from apps.tenants.middleware import get_current_tenant


class ReviewDashboardView(APIView):
    """Summary counts for analyst dashboard."""

    def get(self, request):
        tenant = get_current_tenant() or request.user.tenant
        qs = ActivityRecord.objects.filter(tenant=tenant)
        data = {
            "total": qs.count(),
            "pending": qs.filter(status=ReviewStatus.PENDING).count(),
            "flagged": qs.filter(status=ReviewStatus.FLAGGED).count(),
            "approved": qs.filter(status=ReviewStatus.APPROVED).count(),
            "locked": qs.filter(status=ReviewStatus.LOCKED).count(),
            "by_source": {
                src: qs.filter(source_type=src).count()
                for src, _ in ActivityRecord._meta.get_field("source_type").choices
            },
            "by_scope": {
                scope: qs.filter(scope=scope).count()
                for scope, _ in ActivityRecord._meta.get_field("scope").choices
            },
        }
        return Response(data)


class BulkReviewSerializer(serializers.Serializer):
    activity_ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    action = serializers.ChoiceField(choices=["approve", "flag", "lock"])
    flag_reason = serializers.CharField(required=False, allow_blank=True)
    analyst_notes = serializers.CharField(required=False, allow_blank=True)


class BulkReviewView(APIView):
    def post(self, request):
        serializer = BulkReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = get_current_tenant() or request.user.tenant
        ids = serializer.validated_data["activity_ids"]
        action = serializer.validated_data["action"]

        activities = ActivityRecord.objects.filter(tenant=tenant, id__in=ids)
        if activities.count() != len(ids):
            return Response({"detail": "Some activity IDs not found"}, status=status.HTTP_400_BAD_REQUEST)

        updated = []
        with transaction.atomic():
            for activity in activities:
                if action == "approve":
                    if activity.status == ReviewStatus.LOCKED:
                        continue
                    activity.status = ReviewStatus.APPROVED
                    audit_action = AuditLog.Action.APPROVED
                elif action == "flag":
                    activity.status = ReviewStatus.FLAGGED
                    activity.flag_reason = serializer.validated_data.get("flag_reason", activity.flag_reason)
                    audit_action = AuditLog.Action.FLAGGED
                elif action == "lock":
                    if activity.status != ReviewStatus.APPROVED:
                        continue
                    activity.status = ReviewStatus.LOCKED
                    audit_action = AuditLog.Action.LOCKED

                notes = serializer.validated_data.get("analyst_notes")
                if notes:
                    activity.analyst_notes = notes

                activity.reviewed_by = request.user
                activity.reviewed_at = timezone.now()
                activity.save()

                AuditLog.objects.create(
                    tenant=tenant,
                    activity=activity,
                    actor=request.user,
                    action=audit_action,
                    details={"bulk_action": action},
                )
                updated.append(activity)

        return Response(ActivityRecordSerializer(updated, many=True).data)


class ActivityEditView(APIView):
    def patch(self, request, pk):
        tenant = get_current_tenant() or request.user.tenant
        try:
            activity = ActivityRecord.objects.get(pk=pk, tenant=tenant)
        except ActivityRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if activity.status == ReviewStatus.LOCKED:
            return Response({"detail": "Locked records cannot be edited"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ActivityRecordUpdateSerializer(activity, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        old_values = {f: getattr(activity, f) for f in serializer.validated_data}
        serializer.save(is_edited=True)

        AuditLog.objects.create(
            tenant=tenant,
            activity=activity,
            actor=request.user,
            action=AuditLog.Action.EDITED,
            details={"old": {k: str(v) for k, v in old_values.items()}, "new": serializer.validated_data},
        )
        return Response(ActivityRecordSerializer(activity).data)
