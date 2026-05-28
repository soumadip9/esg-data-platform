from django.db import transaction
from django.utils import timezone

from apps.emissions.models import ActivityRecord, AuditLog, DataSourceType, ReviewStatus
from apps.tenants.models import PlantCode

from apps.ingestion.models import IngestionError, IngestionRun
from apps.ingestion.parsers.base import ParseResult, row_hash
from apps.ingestion.parsers.sap import parse_sap_export
from apps.ingestion.parsers.travel import parse_travel_export
from apps.ingestion.parsers.utility import parse_utility_csv


PARSERS = {
    DataSourceType.SAP: parse_sap_export,
    DataSourceType.UTILITY: parse_utility_csv,
    DataSourceType.TRAVEL: parse_travel_export,
}


def _get_plant_lookup(tenant_id) -> dict[str, str]:
    return dict(PlantCode.objects.filter(tenant_id=tenant_id).values_list("code", "name"))


def run_ingestion(run: IngestionRun, file_content: str) -> IngestionRun:
    run.status = IngestionRun.Status.PROCESSING
    run.started_at = timezone.now()
    run.save(update_fields=["status", "started_at"])

    parser = PARSERS.get(run.source_type)
    if not parser:
        run.status = IngestionRun.Status.FAILED
        run.error_summary = f"No parser for source type: {run.source_type}"
        run.completed_at = timezone.now()
        run.save()
        return run

    try:
        if run.source_type == DataSourceType.SAP:
            parse_result: ParseResult = parser(file_content, _get_plant_lookup(run.tenant_id))
        else:
            parse_result = parser(file_content)
    except Exception as exc:
        run.status = IngestionRun.Status.FAILED
        run.error_summary = str(exc)
        run.completed_at = timezone.now()
        run.save()
        return run

    run.rows_total = len(parse_result.activities) + len(parse_result.errors)

    with transaction.atomic():
        for err in parse_result.errors:
            IngestionError.objects.create(
                run=run,
                row_number=err.get("row_number", 0),
                raw_row=err.get("raw_row", ""),
                error_code=err.get("error_code", "UNKNOWN"),
                error_message=err.get("error_message", ""),
            )
            run.rows_failed += 1

        for activity in parse_result.activities:
            hash_val = row_hash(activity.raw_payload)
            if ActivityRecord.objects.filter(
                tenant=run.tenant,
                source_type=run.source_type,
                source_row_hash=hash_val,
            ).exists():
                run.rows_duplicate += 1
                continue

            status = ReviewStatus.FLAGGED if activity.flag_reason else ReviewStatus.PENDING
            if activity.flag_reason:
                run.rows_flagged += 1

            record = ActivityRecord.objects.create(
                tenant=run.tenant,
                source_type=run.source_type,
                ingestion_run=run,
                source_row_hash=hash_val,
                source_reference=activity.source_reference,
                scope=activity.scope,
                category=activity.category,
                activity_date=activity.activity_date,
                period_start=activity.period_start,
                period_end=activity.period_end,
                description=activity.description,
                site_code=activity.site_code,
                site_name=activity.site_name,
                quantity=activity.quantity,
                unit=activity.unit,
                original_quantity=activity.original_quantity,
                original_unit=activity.original_unit,
                emission_factor_ref=activity.emission_factor_ref,
                status=status,
                flag_reason=activity.flag_reason,
                raw_payload=activity.raw_payload,
            )
            AuditLog.objects.create(
                tenant=run.tenant,
                activity=record,
                ingestion_run=run,
                actor=run.uploaded_by,
                action=AuditLog.Action.CREATED,
                details={"source_type": run.source_type, "filename": run.filename},
            )
            run.rows_success += 1

        AuditLog.objects.create(
            tenant=run.tenant,
            ingestion_run=run,
            actor=run.uploaded_by,
            action=AuditLog.Action.CREATED,
            details={
                "event": "ingestion_completed",
                "rows_success": run.rows_success,
                "rows_failed": run.rows_failed,
                "rows_flagged": run.rows_flagged,
                "rows_duplicate": run.rows_duplicate,
            },
        )

    if run.rows_failed and run.rows_success:
        run.status = IngestionRun.Status.PARTIAL
    elif run.rows_failed and not run.rows_success:
        run.status = IngestionRun.Status.FAILED
        run.error_summary = f"{run.rows_failed} rows failed to parse"
    else:
        run.status = IngestionRun.Status.COMPLETED

    run.completed_at = timezone.now()
    run.save()
    return run
