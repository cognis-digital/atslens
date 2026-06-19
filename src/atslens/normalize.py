"""Field normalization for candidate records.

Normalization operates on *canonical* field names: it tidies names, coerces
dates to ISO (YYYY-MM-DD), standardizes phone numbers, and lowercases emails.
It is deliberately conservative — if a value cannot be confidently normalized
it is left unchanged so validation can still flag it.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from .schema import CANONICAL_SCHEMA, is_iso_date


_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def normalize_name(value: Any) -> Any:
    """Trim, collapse internal whitespace, and title-case a person name."""
    if not isinstance(value, str):
        return value
    cleaned = re.sub(r"\s+", " ", value).strip()
    if not cleaned:
        return cleaned
    # Title-case each whitespace/hyphen-separated part, preserving hyphens.
    parts = re.split(r"(\s|-)", cleaned)
    return "".join(p.capitalize() if p not in (" ", "-") else p for p in parts)


def normalize_email(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return value.strip().lower()


def normalize_phone(value: Any) -> Any:
    """Render a phone as a compact international-ish string.

    Keeps a leading '+' if present, strips other punctuation. Returns the
    original value if there are no usable digits.
    """
    if not isinstance(value, str):
        return value
    has_plus = value.strip().startswith("+")
    digits = re.sub(r"\D", "", value)
    if not digits:
        return value
    return ("+" if has_plus else "") + digits


def normalize_date(value: Any) -> Any:
    """Coerce common date forms to ISO YYYY-MM-DD; leave unknown forms as-is."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if is_iso_date(text):
        return text

    # MM/DD/YYYY or M/D/YYYY
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if m:
        month, day, year = (int(g) for g in m.groups())
        return _build_iso(year, month, day, fallback=text)

    # DD-MM-YYYY (dash form, day first) — distinct from ISO by field widths
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", text)
    if m:
        day, month, year = (int(g) for g in m.groups())
        return _build_iso(year, month, day, fallback=text)

    # "Jan 5, 2026" / "5 Jan 2026"
    m = re.match(r"^([A-Za-z]{3,})\.?\s+(\d{1,2}),?\s+(\d{4})$", text)
    if m and m.group(1)[:3].lower() in _MONTHS:
        month = _MONTHS[m.group(1)[:3].lower()]
        return _build_iso(int(m.group(3)), month, int(m.group(2)), fallback=text)
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3,})\.?\s+(\d{4})$", text)
    if m and m.group(2)[:3].lower() in _MONTHS:
        month = _MONTHS[m.group(2)[:3].lower()]
        return _build_iso(int(m.group(3)), month, int(m.group(1)), fallback=text)

    return value


def _build_iso(year: int, month: int, day: int, fallback: str) -> str:
    iso = f"{year:04d}-{month:02d}-{day:02d}"
    return iso if is_iso_date(iso) else fallback


# Map canonical type -> normalizer. Names use a per-field override below.
_TYPE_NORMALIZERS = {
    "email": normalize_email,
    "phone": normalize_phone,
    "date": normalize_date,
}

_FIELD_NORMALIZERS = {
    "first_name": normalize_name,
    "last_name": normalize_name,
}


def normalize_record(
    record: dict[str, Any],
    schema: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a normalized copy of a canonical-keyed record."""
    if schema is None:
        schema = CANONICAL_SCHEMA
    out = dict(record)
    for field, value in record.items():
        if field in _FIELD_NORMALIZERS:
            out[field] = _FIELD_NORMALIZERS[field](value)
            continue
        spec = schema.get(field)
        if spec is not None:
            normalizer = _TYPE_NORMALIZERS.get(spec["type"])
            if normalizer is not None:
                out[field] = normalizer(value)
    return out


def normalize_records(
    records: Iterable[dict[str, Any]],
    schema: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return [normalize_record(r, schema) for r in records]
