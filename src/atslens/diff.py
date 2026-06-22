"""Record-set diffing for migration verification.

When you move candidate data between two ATS systems, you want to *prove* the
migration was faithful: the same candidates are present, and the fields that
should have carried over actually did. ``compute_diff`` compares two
canonical-keyed record sets keyed by ``candidate_id`` and reports, per
candidate, which fields were added, removed, or changed — plus which
candidates appeared or disappeared entirely.

The diff is deliberately schema-aware but format-agnostic: feed it canonical
records (map vendor exports to ``canonical`` first) so field names line up.
"""

from __future__ import annotations

from typing import Any, Iterable


_DEFAULT_KEY = "candidate_id"


def _index_by_key(
    records: Iterable[dict[str, Any]], key: str
) -> dict[str, dict[str, Any]]:
    """Index records by their key field. Records missing the key are skipped
    into a synthetic bucket so they still surface in the diff."""
    indexed: dict[str, dict[str, Any]] = {}
    unkeyed = 0
    for record in records:
        if not isinstance(record, dict):
            continue
        value = record.get(key)
        if value in (None, ""):
            unkeyed += 1
            indexed[f"<unkeyed#{unkeyed}>"] = record
        else:
            indexed[str(value)] = record
    return indexed


def diff_record(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Field-level diff between two records.

    Returns a mapping ``field -> {"before": x, "after": y}`` for every field
    whose value changed, was added, or was removed. Empty when identical.
    """
    changes: dict[str, dict[str, Any]] = {}
    for field in sorted(set(before) | set(after)):
        in_before = field in before
        in_after = field in after
        old = before.get(field)
        new = after.get(field)
        if in_before and in_after:
            if old != new:
                changes[field] = {"before": old, "after": new}
        elif in_after:
            changes[field] = {"before": None, "after": new}
        else:
            changes[field] = {"before": old, "after": None}
    return changes


def compute_diff(
    before: Iterable[dict[str, Any]],
    after: Iterable[dict[str, Any]],
    key: str = _DEFAULT_KEY,
) -> dict[str, Any]:
    """Compare two record sets keyed by ``key``.

    Returns a structured report::

        {
          "key": "candidate_id",
          "added":   [<key>, ...],        # present only in `after`
          "removed": [<key>, ...],        # present only in `before`
          "changed": {<key>: {field: {"before":.., "after":..}}, ...},
          "unchanged": [<key>, ...],
          "summary": {"added": n, "removed": n, "changed": n,
                      "unchanged": n, "total_before": n, "total_after": n},
        }
    """
    before_idx = _index_by_key(before, key)
    after_idx = _index_by_key(after, key)

    before_keys = set(before_idx)
    after_keys = set(after_idx)

    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)

    changed: dict[str, dict[str, Any]] = {}
    unchanged: list[str] = []
    for k in sorted(before_keys & after_keys):
        field_changes = diff_record(before_idx[k], after_idx[k])
        if field_changes:
            changed[k] = field_changes
        else:
            unchanged.append(k)

    return {
        "key": key,
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "unchanged": len(unchanged),
            "total_before": len(before_keys),
            "total_after": len(after_keys),
        },
    }


def diff_is_clean(report: dict[str, Any]) -> bool:
    """True when the two record sets are identical (a faithful migration)."""
    s = report["summary"]
    return s["added"] == 0 and s["removed"] == 0 and s["changed"] == 0
