"""Command-line interface for atslens.

Subcommands:
    map       remap records between field layouts
    validate  check records against a schema
    export    write records to CSV or JSON
    diff      compare two record sets to verify a migration
    layouts   list known field layouts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .diff import compute_diff, diff_is_clean
from .exporter import to_csv, to_json, write_export
from .layouts import list_layouts, resolve_layout
from .mapper import map_records, _to_canonical
from .normalize import normalize_records
from .schema import CANONICAL_SCHEMA, validate_records


def _load_records(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array or object of records")
    return data


def _emit(text: str, out_path: str | None) -> None:
    if out_path:
        Path(out_path).write_text(text, encoding="utf-8", newline="")
        print(f"wrote {out_path}", file=sys.stderr)
    else:
        print(text)


# --- subcommand handlers ----------------------------------------------------

def cmd_map(args: argparse.Namespace) -> int:
    records = _load_records(args.records)
    source = resolve_layout(args.profile) if args.profile else resolve_layout(args.from_)
    dest = resolve_layout(args.to)
    if args.normalize:
        # Normalize on canonical keys, then map out to the destination layout.
        from .mapper import _to_canonical, _from_canonical
        canonical = [_to_canonical(r, source) for r in records]
        canonical = normalize_records(canonical)
        mapped = [_from_canonical(r, dest) for r in canonical]
    else:
        mapped = map_records(records, source, dest)
    _emit(to_json(mapped), args.output)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    records = _load_records(args.records)
    if args.normalize:
        records = normalize_records(records)
    # schema is always canonical in this build; flag kept for forward-compat.
    problems = validate_records(records, CANONICAL_SCHEMA)
    if args.json:
        print(json.dumps({"valid": not problems, "problems": problems}, indent=2))
    else:
        if problems:
            print(f"INVALID: {len(problems)} problem(s)")
            for problem in problems:
                print(f"  - {problem}")
        else:
            print(f"VALID: {len(records)} record(s) conform to '{args.schema}'")
    return 1 if problems else 0


def cmd_export(args: argparse.Namespace) -> int:
    records = _load_records(args.records)
    if args.normalize:
        records = normalize_records(records)
    if args.output:
        write_export(records, args.format, args.output)
        print(f"wrote {len(records)} record(s) to {args.output}", file=sys.stderr)
    else:
        text = to_csv(records) if args.format == "csv" else to_json(records)
        print(text)
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    before = _load_records(args.before)
    after = _load_records(args.after)
    # Optionally translate each side from a vendor layout into canonical names
    # so fields line up before comparing.
    if args.from_before:
        layout = resolve_layout(args.from_before)
        before = [_to_canonical(r, layout) for r in before]
    if args.from_after:
        layout = resolve_layout(args.from_after)
        after = [_to_canonical(r, layout) for r in after]
    if args.normalize:
        before = normalize_records(before)
        after = normalize_records(after)
    report = compute_diff(before, after, key=args.key)
    clean = diff_is_clean(report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        s = report["summary"]
        verdict = "CLEAN" if clean else "DIFFERENCES"
        print(
            f"{verdict}: {s['total_before']} -> {s['total_after']} record(s) "
            f"(added {s['added']}, removed {s['removed']}, "
            f"changed {s['changed']}, unchanged {s['unchanged']})"
        )
        for k in report["added"]:
            print(f"  + {k}  (only in after)")
        for k in report["removed"]:
            print(f"  - {k}  (only in before)")
        for k, fields in report["changed"].items():
            print(f"  ~ {k}")
            for field, ba in fields.items():
                print(f"      {field}: {ba['before']!r} -> {ba['after']!r}")
    return 0 if clean else 1


def cmd_layouts(args: argparse.Namespace) -> int:
    layouts = list_layouts()
    if args.json:
        payload = [
            {"name": l.name, "description": l.description, "fields": l.fields}
            for l in layouts
        ]
        print(json.dumps(payload, indent=2))
        return 0
    for layout in layouts:
        print(f"{layout.name}: {layout.description}")
        for canonical_field in CANONICAL_SCHEMA:
            vendor = layout.to_vendor_key(canonical_field)
            arrow = "=" if vendor == canonical_field else "->"
            print(f"    {canonical_field:<18} {arrow} {vendor}")
        print()
    return 0


# --- parser -----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="atslens",
        description="ATS field-schema mapper & exporter for candidate-data "
        "portability.",
    )
    parser.add_argument("--version", action="version",
                        version=f"atslens {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    # map
    p_map = sub.add_parser("map", help="remap records between field layouts")
    p_map.add_argument("records", help="path to records JSON")
    p_map.add_argument("--from", dest="from_", default="canonical",
                       help="source layout name (default: canonical)")
    p_map.add_argument("--to", required=True, help="destination layout name")
    p_map.add_argument("--profile", default=None,
                       help="custom source profile JSON (overrides --from)")
    p_map.add_argument("--normalize", action="store_true",
                       help="normalize fields before mapping")
    p_map.add_argument("--json", action="store_true",
                       help="emit JSON (default output is JSON)")
    p_map.add_argument("-o", "--output", default=None,
                       help="write to file instead of stdout")
    p_map.set_defaults(func=cmd_map)

    # validate
    p_val = sub.add_parser("validate", help="validate records against a schema")
    p_val.add_argument("records", help="path to records JSON")
    p_val.add_argument("--schema", default="canonical",
                       help="schema name (default: canonical)")
    p_val.add_argument("--normalize", action="store_true",
                       help="normalize before validating")
    p_val.add_argument("--json", action="store_true", help="emit JSON report")
    p_val.set_defaults(func=cmd_validate)

    # export
    p_exp = sub.add_parser("export", help="export records to CSV or JSON")
    p_exp.add_argument("records", help="path to records JSON")
    p_exp.add_argument("--format", choices=("csv", "json"), default="csv",
                       help="output format (default: csv)")
    p_exp.add_argument("--normalize", action="store_true",
                       help="normalize before exporting")
    p_exp.add_argument("-o", "--output", default=None,
                       help="write to file instead of stdout")
    p_exp.set_defaults(func=cmd_export)

    # diff
    p_diff = sub.add_parser(
        "diff",
        help="diff two record sets to verify a migration round-tripped",
    )
    p_diff.add_argument("before", help="path to baseline records JSON")
    p_diff.add_argument("after", help="path to records JSON to compare")
    p_diff.add_argument("--key", default="candidate_id",
                        help="record key field (default: candidate_id)")
    p_diff.add_argument("--from-before", dest="from_before", default=None,
                        help="layout/profile to translate 'before' from")
    p_diff.add_argument("--from-after", dest="from_after", default=None,
                        help="layout/profile to translate 'after' from")
    p_diff.add_argument("--normalize", action="store_true",
                        help="normalize both sides before comparing")
    p_diff.add_argument("--json", action="store_true",
                        help="emit JSON diff report")
    p_diff.set_defaults(func=cmd_diff)

    # layouts
    p_lay = sub.add_parser("layouts", help="list known field layouts")
    p_lay.add_argument("--json", action="store_true", help="emit JSON")
    p_lay.set_defaults(func=cmd_layouts)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
