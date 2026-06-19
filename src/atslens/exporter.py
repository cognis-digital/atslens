"""Export candidate records to CSV or JSON.

CSV export produces a stable, union-of-keys header so heterogeneous records
still round-trip predictably. JSON export is pretty-printed UTF-8.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable, Sequence


def _collect_fieldnames(
    records: Sequence[dict[str, Any]],
    fieldnames: Sequence[str] | None,
) -> list[str]:
    if fieldnames is not None:
        return list(fieldnames)
    # Preserve first-seen order across all records (stable union of keys).
    ordered: list[str] = []
    seen: set[str] = set()
    for record in records:
        for key in record:
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    return ordered


def to_csv(
    records: Iterable[dict[str, Any]],
    fieldnames: Sequence[str] | None = None,
) -> str:
    """Serialize records to a CSV string (header + rows)."""
    records = list(records)
    names = _collect_fieldnames(records, fieldnames)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=names, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    for record in records:
        # Render non-string scalars deterministically; leave strings intact.
        row = {
            key: ("" if value is None else value)
            for key, value in record.items()
            if key in names
        }
        writer.writerow(row)
    return buffer.getvalue()


def to_json(records: Iterable[dict[str, Any]], indent: int = 2) -> str:
    """Serialize records to a pretty JSON string."""
    return json.dumps(list(records), indent=indent, ensure_ascii=False)


def write_export(
    records: Iterable[dict[str, Any]],
    fmt: str,
    out_path: str,
    fieldnames: Sequence[str] | None = None,
) -> str:
    """Write records to out_path in the given format; return the text written."""
    records = list(records)
    if fmt == "csv":
        text = to_csv(records, fieldnames)
    elif fmt == "json":
        text = to_json(records)
    else:
        raise ValueError(f"unknown export format '{fmt}' (use csv or json)")
    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    return text
