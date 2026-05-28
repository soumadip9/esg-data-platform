"""Parser for utility portal CSV exports (Green Button / consolidated billing style)."""

import csv
import io
from datetime import datetime

from apps.emissions.models import ActivityCategory, EmissionScope

from ..services.units import CANONICAL_UNITS, convert_quantity, normalize_unit, parse_decimal
from .base import ParseResult, ParsedActivity

COLUMN_ALIASES = {
    "meter": "meter_id",
    "meter id": "meter_id",
    "meter_id": "meter_id",
    "account": "account_number",
    "account number": "account_number",
    "service address": "service_address",
    "start date": "period_start",
    "end date": "period_end",
    "bill start": "period_start",
    "bill end": "period_end",
    "billing period start": "period_start",
    "billing period end": "period_end",
    "usage": "usage",
    "consumption": "usage",
    "kwh": "usage",
    "units": "unit",
    "unit": "unit",
    "type": "resource_type",
    "estimated": "is_estimated",
    "read type": "read_type",
    "facility": "facility_name",
    "site": "facility_name",
}


def _parse_date(value: str):
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date: {value}")


def _normalize_headers(fieldnames: list[str]) -> dict[str, str]:
    mapping = {}
    for h in fieldnames:
        key = h.strip().lower()
        mapping[h] = COLUMN_ALIASES.get(key, key.replace(" ", "_"))
    return mapping


def parse_utility_csv(content: str) -> ParseResult:
    result = ParseResult()
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames:
        result.errors.append({"row_number": 0, "error_code": "EMPTY_FILE", "error_message": "No header row"})
        return result

    header_map = _normalize_headers(reader.fieldnames)

    for row_num, raw_row in enumerate(reader, start=2):
        try:
            row = {header_map.get(k, k): (v.strip() if v else "") for k, v in raw_row.items()}
            resource = row.get("resource_type", "electricity").lower()
            if resource and resource not in ("electricity", "electric", "power", ""):
                continue

            usage = parse_decimal(row.get("usage", ""))
            unit = normalize_unit(row.get("unit", "kWh") or "KWH")
            target = CANONICAL_UNITS["electricity"]

            try:
                normalized = convert_quantity(usage, unit, target)
            except ValueError:
                normalized = usage
                target = unit
                flag = f"Unknown unit '{unit}'"
            else:
                flag = ""

            period_start = _parse_date(row.get("period_start", ""))
            period_end = _parse_date(row.get("period_end", ""))

            read_type = row.get("read_type", row.get("is_estimated", "")).lower()
            if read_type in ("estimated", "e", "yes", "true", "1"):
                flag = (flag + "; Estimated meter read").strip("; ")

            if period_end.day < 28 and (period_end - period_start).days > 35:
                flag = (flag + "; Billing period spans >35 days").strip("; ")

            meter_id = row.get("meter_id", row.get("account_number", "UNKNOWN"))

            result.activities.append(
                ParsedActivity(
                    source_reference=meter_id,
                    scope=EmissionScope.SCOPE_2,
                    category=ActivityCategory.ELECTRICITY,
                    activity_date=period_end,
                    period_start=period_start,
                    period_end=period_end,
                    quantity=normalized,
                    unit=target,
                    original_quantity=usage,
                    original_unit=unit,
                    description=f"Electricity — {row.get('facility_name', row.get('service_address', ''))}",
                    site_code=row.get("account_number", ""),
                    site_name=row.get("facility_name", row.get("service_address", "")),
                    emission_factor_ref="grid_average",
                    flag_reason=flag,
                    raw_payload=row,
                )
            )
        except Exception as exc:
            result.errors.append(
                {
                    "row_number": row_num,
                    "error_code": "PARSE_ERROR",
                    "error_message": str(exc),
                    "raw_row": str(raw_row),
                }
            )

    return result
