from django.core.management.base import BaseCommand, CommandError

from apps.emissions.models import ActivityRecord, AuditLog
from apps.ingestion.models import IngestionRun
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = "Delete all ingestion and activity data for a tenant (keeps tenant, users, plant codes)"

    def add_arguments(self, parser):
        parser.add_argument("tenant_slug", type=str, help="Tenant slug, e.g. globex-ind")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show counts without deleting",
        )

    def handle(self, *args, **options):
        slug = options["tenant_slug"]
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist as exc:
            raise CommandError(f"Tenant not found: {slug}") from exc

        activities = ActivityRecord.objects.filter(tenant=tenant)
        runs = IngestionRun.objects.filter(tenant=tenant)
        audit_logs = AuditLog.objects.filter(tenant=tenant)

        act_count = activities.count()
        run_count = runs.count()
        log_count = audit_logs.count()

        if options["dry_run"]:
            self.stdout.write(
                f"[dry-run] {tenant.name}: {act_count} activities, "
                f"{run_count} ingestion runs, {log_count} audit logs"
            )
            return

        activities.delete()
        AuditLog.objects.filter(tenant=tenant).delete()
        runs.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleared {tenant.name}: {act_count} activities, "
                f"{run_count} ingestion runs, {log_count} audit logs"
            )
        )
