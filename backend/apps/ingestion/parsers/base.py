import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass
class ParsedActivity:
    source_reference: str
    scope: str
    category: str
    activity_date: date
    quantity: Decimal
    unit: str
    description: str = ""
    site_code: str = ""
    site_name: str = ""
    period_start: date | None = None
    period_end: date | None = None
    original_quantity: Decimal | None = None
    original_unit: str = ""
    emission_factor_ref: str = ""
    flag_reason: str = ""
    raw_payload: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    activities: list[ParsedActivity] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


def row_hash(payload: dict) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()
