from celery import shared_task

from apps.ingestion.models import IngestionRun
from apps.ingestion.services.pipeline import run_ingestion


@shared_task(bind=True, max_retries=2)
def process_ingestion_task(self, run_id: str, file_content: str):
    try:
        run = IngestionRun.objects.get(id=run_id)
        run_ingestion(run, file_content)
    except IngestionRun.DoesNotExist:
        return
    except Exception as exc:
        run = IngestionRun.objects.filter(id=run_id).first()
        if run:
            run.status = IngestionRun.Status.FAILED
            run.error_summary = str(exc)
            run.save(update_fields=["status", "error_summary"])
        raise self.retry(exc=exc, countdown=5)
