"""Remap candidate records between field layouts.

The mapper always routes through the canonical schema: records keyed by the
source layout's vendor names are first translated to canonical names, then to
the destination layout's vendor names. This keeps round-trips lossless for
fields both layouts share.
"""

from __future__ import annotations

from typing import Any, Iterable

from .layouts import Layout


def _to_canonical(record: dict[str, Any], source: Layout) -> dict[str, Any]:
    """Translate a record keyed by source vendor names to canonical names."""
    out: dict[str, Any] = {}
    for vendor_key, value in record.items():
        canonical_key = source.to_canonical_key(vendor_key)
        out[canonical_key] = value
    return out


def _from_canonical(record: dict[str, Any], dest: Layout) -> dict[str, Any]:
    """Translate a canonical-keyed record to destination vendor names."""
    out: dict[str, Any] = {}
    for canonical_key, value in record.items():
        out[dest.to_vendor_key(canonical_key)] = value
    return out


def map_record(
    record: dict[str, Any],
    source: Layout,
    dest: Layout,
) -> dict[str, Any]:
    """Remap a single record from the source layout to the destination layout."""
    return _from_canonical(_to_canonical(record, source), dest)


def map_records(
    records: Iterable[dict[str, Any]],
    source: Layout,
    dest: Layout,
) -> list[dict[str, Any]]:
    """Remap many records from the source layout to the destination layout."""
    return [map_record(r, source, dest) for r in records]
