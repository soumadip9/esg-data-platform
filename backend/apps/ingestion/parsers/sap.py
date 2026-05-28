"""Parser for SAP ME80FN tab-delimited procurement export (EKKO/EKPO fields)."""

import csv
import io
from datetime import datetime
from decimal import Decimal

from apps.emissions.models import ActivityCategory, EmissionScope

from ..services.units import CANONICAL_UNITS, convert_quantity, normalize_unit, parse_decimal
from .base import ParseResult, ParsedActivity

# SAP field aliases — handles German and English column headers
COLUMN_MAP = {
    "EBELN": "po_number",
    "EBELP": "item_number",
    "BEDAT": "document_date",
    "BSART": "doc_type",
    "MATNR": "material_number",
    "TXZ01": "short_text",
    "MATKL": "material_group",
    "WERKS": "plant",
    "MENGE": "quantity",
    "MEINS": "unit",
    "NETWR": "net_value",
    "LIFNR": "vendor",
    "EKORG": "purch_org",
    # German variants seen in EU deployments
    "BESTELLUNG": "po_number",
    "MATERIAL": "material_number",
    "MENGE_BEST": "quantity",
    "EINHEIT": "unit",
    "WERK": "plant",
    "BELEGDATUM": "document_date",
}

FUEL_MATERIAL_GROUPS = {"0101", "0102", "0201", "FUEL", "ENERGY"}
FUEL_KEYWORDS = {"diesel", "gasoline", "petrol", "fuel", "heating oil", "kerosene", "lpg", "natural gas"}


def _parse_sap_date(value: str):
    value = value.strip()
    for fmt in ("%Y%m%d", "%d.%m.%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized SAP date format: {value}")


def _normalize_row(raw: dict[str, str]) -> dict[str, str]:
    normalized = {}
    for key, val in raw.items():
        clean_key = key.strip().upper().replace(" ", "_")
        mapped = COLUMN_MAP.get(clean_key, clean_key.lower())
        normalized[mapped] = val.strip() if val else ""
    return normalized


def _classify_activity(row: dict) -> tuple[str, str]:
    mat_group = row.get("material_group", "").upper()
    text = row.get("short_text", "").lower()
    doc_type = row.get("doc_type", "").upper()

    if mat_group in FUEL_MATERIAL_GROUPS or any(kw in text for kw in FUEL_KEYWORDS):
        return EmissionScope.SCOPE_1, ActivityCategory.FUEL
    if doc_type in ("ZNB", "NB") or mat_group:
        return EmissionScope.SCOPE_3, ActivityCategory.PROCUREMENT
    return EmissionScope.SCOPE_3, ActivityCategory.PROCUREMENT


def parse_sap_export(content: str, plant_lookup: dict[str, str] | None = None) -> ParseResult:
    plant_lookup = plant_lookup or {}
    result = ParseResult()
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")

    if not reader.fieldnames:
        result.errors.append({"row_number": 0, "error_code": "EMPTY_FILE", "error_message": "No header row found"})
        return result

    for row_num, raw_row in enumerate(reader, start=2):
        try:
            row = _normalize_row(raw_row)
            if not any(row.values()):
                continue

            qty = parse_decimal(row.get("quantity", ""))
            unit = normalize_unit(row.get("unit", ""))
            scope, category = _classify_activity(row)
            target_unit = CANONICAL_UNITS.get(category if isinstance(category, str) else category.value, unit)

            try:
                normalized_qty = convert_quantity(qty, unit, target_unit)
            except ValueError:
                normalized_qty = qty
                target_unit = unit
                flag = f"Unknown unit '{unit}' — stored as-is"
            else:
                flag = ""

            plant = row.get("plant", "")
            site_name = plant_lookup.get(plant, "")

            activity_date = _parse_sap_date(row.get("document_date", ""))
            po = row.get("po_number", "")
            item = row.get("item_number", "00010")

            if qty > Decimal("100000") and category == ActivityCategory.FUEL:
                flag = (flag + "; Unusually high fuel quantity — verify").strip("; ")

            result.activities.append(
                ParsedActivity(
                    source_reference=f"{po}/{item}",
                    scope=scope,
                    category=category,
                    activity_date=activity_date,
                    quantity=normalized_qty,
                    unit=target_unit,
                    original_quantity=qty,
                    original_unit=unit,
                    description=row.get("short_text", "") or row.get("material_number", ""),
                    site_code=plant,
                    site_name=site_name,
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
