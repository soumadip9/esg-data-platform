from pathlib import Path

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.ingestion.models import IngestionRun
from apps.ingestion.services.pipeline import run_ingestion


def _resolve_sample(path: str) -> Path | None:
    candidates = [
        Path(path),
        Path(__file__).resolve().parents[5] / path,
        Path("/app") / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


class Command(BaseCommand):
    help = "Load sample data files from /sample_data into the demo tenant"

    def handle(self, *args, **options):
        user = User.objects.get(username="analyst")
        tenant = user.tenant
        samples = [
            ("sap", "sample_data/sap_procurement.tsv"),
            ("utility", "sample_data/utility_electricity.csv"),
            ("travel", "sample_data/travel_expense.txt"),
        ]
        for source_type, path in samples:
            resolved = _resolve_sample(path)
            if not resolved:
                self.stderr.write(f"File not found: {path}")
                continue
            with open(resolved, encoding="utf-8") as f:
                content = f.read()
            run = IngestionRun.objects.create(
                tenant=tenant,
                source_type=source_type,
                filename=resolved.name,
                uploaded_by=user,
            )
            run_ingestion(run, content)
            self.stdout.write(
                self.style.SUCCESS(
                    f"{source_type}: {run.rows_success} ingested, "
                    f"{run.rows_flagged} flagged, {run.rows_failed} failed"
                )
            )
