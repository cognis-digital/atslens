"""Canonical candidate schema and validation logic.

The canonical schema is the neutral, vendor-independent representation of a
candidate record. Every vendor layout maps to and from these field names.
"""

from __future__ import annotations

import re
from typing import Any, Iterable


# --- format helpers ---------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-().]{5,}$")


def is_email(value: Any) -> bool:
    return isinstance(value, str) and bool(_EMAIL_RE.match(value.strip()))


def is_iso_date(value: Any) -> bool:
    """True if value is an ISO calendar date (YYYY-MM-DD) that is real."""
    if not isinstance(value, str) or not _DATE_RE.match(value):
        return False
    year, month, day = (int(p) for p in value.split("-"))
    if not (1 <= month <= 12):
        return False
    days_in_month = [31, 29 if _is_leap(year) else 28, 31, 30, 31, 30,
                     31, 31, 30, 31, 30, 31]
    return 1 <= day <= days_in_month[month - 1]


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def is_phone(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    digits = re.sub(r"\D", "", value)
    return bool(_PHONE_RE.match(value.strip())) and 7 <= len(digits) <= 15


# --- canonical schema -------------------------------------------------------

# Each field declares: type, whether required, and an optional format check.
# Supported types: "string", "integer", "number", "email", "date", "phone".
CANONICAL_SCHEMA: dict[str, dict[str, Any]] = {
    "candidate_id": {"type": "string", "required": True},
    "first_name": {"type": "string", "required": True},
    "last_name": {"type": "string", "required": True},
    "email": {"type": "email", "required": True},
    "phone": {"type": "phone", "required": False},
    "applied_date": {"type": "date", "required": False},
    "job_title": {"type": "string", "required": False},
    "location": {"type": "string", "required": False},
    "years_experience": {"type": "integer", "required": False},
    "source": {"type": "string", "required": False},
    "status": {"type": "string", "required": False},
}

_TYPE_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "email": is_email,
    "date": is_iso_date,
    "phone": is_phone,
}


class ValidationError(Exception):
    """Raised when records fail schema validation.

    Carries the structured list of problems for callers that want detail.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__(
            f"{len(problems)} validation problem(s):\n  "
            + "\n  ".join(problems)
        )


def validate_records(
    records: Iterable[dict[str, Any]],
    schema: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    """Validate records against a schema.

    Returns a list of human-readable problem strings (empty == all valid).
    Does not raise; callers decide what to do with the result.
    """
    if schema is None:
        schema = CANONICAL_SCHEMA

    problems: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            problems.append(f"record[{index}]: not an object")
            continue
        for field, spec in schema.items():
            present = field in record and record[field] not in (None, "")
            if spec.get("required") and not present:
                problems.append(
                    f"record[{index}]: missing required field '{field}'"
                )
                continue
            if not present:
                continue
            value = record[field]
            check = _TYPE_CHECKS.get(spec["type"])
            if check is not None and not check(value):
                problems.append(
                    f"record[{index}]: field '{field}' failed "
                    f"{spec['type']} check (got {value!r})"
                )
    return problems
