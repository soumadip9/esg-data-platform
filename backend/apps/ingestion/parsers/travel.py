"""Parser for Concur-style pipe-delimited travel expense export (SAE subset)."""

import csv
import io
from datetime import datetime
from decimal import Decimal

from apps.emissions.models import ActivityCategory, EmissionScope

from ..services.units import parse_decimal
from .base import ParseResult, ParsedActivity

# Approximate airport distances (km) for common routes when distance not provided
AIRPORT_DISTANCE_ESTIMATES = {
    ("JFK", "LHR"): 5540,
    ("SFO", "ORD"): 2960,
    ("LAX", "JFK"): 3970,
    ("FRA", "MUC"): 300,
    ("DEL", "BOM"): 1150,
    ("SIN", "HKG"): 2580,
}

EXPENSE_TYPE_MAP = {
    "airfare": ActivityCategory.TRAVEL_AIR,
    "air": ActivityCategory.TRAVEL_AIR,
    "flight": ActivityCategory.TRAVEL_AIR,
    "hotel": ActivityCategory.TRAVEL_HOTEL,
    "lodging": ActivityCategory.TRAVEL_HOTEL,
    "car rental": ActivityCategory.TRAVEL_GROUND,
    "ground transport": ActivityCategory.TRAVEL_GROUND,
    "mileage": ActivityCategory.TRAVEL_GROUND,
    "taxi": ActivityCategory.TRAVEL_GROUND,
    "rail": ActivityCategory.TRAVEL_GROUND,
}


def _parse_date(value: str):
    value = value.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date: {value}")


def _estimate_flight_distance(origin: str, destination: str) -> tuple[Decimal | None, str]:
    origin = origin.strip().upper()[:3]
    dest = destination.strip().upper()[:3]
    if not origin or not dest:
        return None, "Missing airport codes — distance unknown"
    key = (origin, dest)
    rev_key = (dest, origin)
    if key in AIRPORT_DISTANCE_ESTIMATES:
        return Decimal(str(AIRPORT_DISTANCE_ESTIMATES[key])), ""
    if rev_key in AIRPORT_DISTANCE_ESTIMATES:
        return Decimal(str(AIRPORT_DISTANCE_ESTIMATES[rev_key])), ""
    return None, f"No distance table entry for {origin}-{dest}"


def parse_travel_export(content: str, delimiter: str = "|") -> ParseResult:
    result = ParseResult()
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

    if not reader.fieldnames:
        result.errors.append({"row_number": 0, "error_code": "EMPTY_FILE", "error_message": "No header row"})
        return result

    # Normalize headers to lowercase with underscores
    field_map = {h: h.strip().lower().replace(" ", "_") for h in reader.fieldnames}

    for row_num, raw_row in enumerate(reader, start=2):
        try:
            row = {field_map[k]: (v.strip() if v else "") for k, v in raw_row.items()}

            expense_type = row.get("expense_type", row.get("entry_type", "")).lower()
            category = None
            for key, cat in EXPENSE_TYPE_MAP.items():
                if key in expense_type:
                    category = cat
                    break
            if not category:
                continue

            txn_date = _parse_date(row.get("transaction_date", row.get("expense_date", "")))
            report_id = row.get("report_id", row.get("report_key", ""))
            entry_id = row.get("entry_id", row.get("entry_key", str(row_num)))
            source_ref = f"{report_id}/{entry_id}" if report_id else entry_id

            flag = ""
            if category == ActivityCategory.TRAVEL_AIR:
                origin = row.get("departure_airport", row.get("from_location", ""))
                dest = row.get("arrival_airport", row.get("to_location", ""))
                distance_str = row.get("distance", row.get("flight_distance", ""))
                if distance_str:
                    quantity = parse_decimal(distance_str)
                    unit = "km"
                else:
                    quantity, flag = _estimate_flight_distance(origin, dest)
                    unit = "km"
                    if quantity is None:
                        quantity = Decimal("1")
                        unit = "segment"
                        flag = flag or "Flight segment without distance"
                description = f"Flight {origin}-{dest}" if origin and dest else expense_type
                factor_ref = "defra_air_domestic" if quantity and quantity < Decimal("1500") else "defra_air_longhaul"

            elif category == ActivityCategory.TRAVEL_HOTEL:
                nights_str = row.get("nights") or row.get("distance_unit") or row.get("quantity") or "1"
                quantity = parse_decimal(nights_str.strip())
                unit = "nights"
                description = row.get("vendor", row.get("merchant", "Hotel"))
                factor_ref = "defra_hotel_night"

            else:
                distance_str = row.get("distance", row.get("mileage", ""))
                if distance_str:
                    quantity = parse_decimal(distance_str)
                    unit_raw = row.get("distance_unit", "mi").lower()
                    unit = "km" if unit_raw in ("km", "kilometers") else "km"
                    if unit_raw in ("mi", "miles"):
                        quantity = quantity * Decimal("1.60934")
                else:
                    amount = row.get("amount", "0")
                    quantity = parse_decimal(amount) if amount else Decimal("1")
                    unit = "trip"
                    flag = "Ground transport without distance — using trip count"
                description = row.get("vendor", row.get("merchant", expense_type))
                factor_ref = "defra_car_average"

            result.activities.append(
                ParsedActivity(
                    source_reference=source_ref,
                    scope=EmissionScope.SCOPE_3,
                    category=category,
                    activity_date=txn_date,
                    quantity=quantity,
                    unit=unit,
                    description=description,
                    site_code=row.get("cost_center", row.get("employee_id", "")),
                    site_name=row.get("employee_name", row.get("employee", "")),
                    emission_factor_ref=factor_ref,
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
