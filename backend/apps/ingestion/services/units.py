"""Unit normalization for emission activity quantities."""

from decimal import Decimal, InvalidOperation

CONVERSIONS = {
    ("GAL", "L"): Decimal("3.78541"),
    ("L", "GAL"): Decimal("0.264172"),
    ("M3", "L"): Decimal("1000"),
    ("L", "M3"): Decimal("0.001"),
    ("KWH", "kWh"): Decimal("1"),
    ("MWH", "kWh"): Decimal("1000"),
    ("GJ", "kWh"): Decimal("277.778"),
    ("THERM", "kWh"): Decimal("29.3071"),
    ("MI", "km"): Decimal("1.60934"),
    ("KM", "km"): Decimal("1"),
    ("MILES", "km"): Decimal("1.60934"),
    ("ST", "kg"): Decimal("907.185"),
    ("KG", "kg"): Decimal("1"),
    ("LB", "kg"): Decimal("0.453592"),
    ("TON", "kg"): Decimal("1000"),
    ("TO", "kg"): Decimal("1000"),
    ("LTR", "L"): Decimal("1"),
    ("EA", "ea"): Decimal("1"),
    ("NIGHT", "nights"): Decimal("1"),
    ("NIGHTS", "nights"): Decimal("1"),
}

CANONICAL_UNITS = {
    "fuel": "L",
    "procurement": "kg",
    "electricity": "kWh",
    "travel_air": "km",
    "travel_hotel": "nights",
    "travel_ground": "km",
}


def normalize_unit(unit: str) -> str:
    if not unit:
        return ""
    return unit.strip().upper().replace(".", "")


def convert_quantity(quantity: Decimal, from_unit: str, to_unit: str) -> Decimal:
    from_u = normalize_unit(from_unit)
    to_u = normalize_unit(to_unit)
    if from_u == to_u:
        return quantity
    key = (from_u, to_u)
    if key in CONVERSIONS:
        return quantity * CONVERSIONS[key]
    raise ValueError(f"No conversion from {from_u} to {to_u}")


def parse_decimal(value: str) -> Decimal:
    if value is None or str(value).strip() == "":
        raise ValueError("Empty numeric value")
    cleaned = str(value).strip().replace(",", "").replace(" ", "")
    if cleaned.startswith("."):
        cleaned = "0" + cleaned
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid number: {value}") from exc
