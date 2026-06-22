"""Test suite for atslens."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atslens import (
    BUILTIN_LAYOUTS,
    compute_diff,
    diff_is_clean,
    diff_record,
    list_layouts,
    load_layout,
    load_profile,
    map_records,
    normalize_record,
    normalize_records,
    to_csv,
    to_json,
    validate_records,
)
from atslens.cli import main
from atslens.mapper import map_record
from atslens.normalize import (
    normalize_date,
    normalize_email,
    normalize_name,
    normalize_phone,
)


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def records():
    return json.loads((EXAMPLES / "records.json").read_text(encoding="utf-8"))


# --- layouts ----------------------------------------------------------------

def test_builtin_layouts_present():
    names = {l.name for l in list_layouts()}
    assert {"canonical", "vendorA", "vendorB"} <= names


def test_load_layout_unknown_raises():
    with pytest.raises(KeyError):
        load_layout("nope")


def test_load_profile_from_file():
    layout = load_profile(EXAMPLES / "custom_profile.json")
    assert layout.name == "vendorC"
    assert layout.to_vendor_key("email") == "Email"
    assert layout.to_canonical_key("Email") == "email"


def test_load_profile_requires_fields(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"name": "x"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_profile(bad)


# --- mapping ----------------------------------------------------------------

def test_map_canonical_to_vendor_a(records):
    canonical = load_layout("canonical")
    vendor_a = load_layout("vendorA")
    mapped = map_records(records, canonical, vendor_a)
    assert "applicantId" in mapped[0]
    assert "emailAddress" in mapped[0]
    assert mapped[0]["applicantId"] == "C-1001"


def test_map_round_trip_lossless(records):
    canonical = load_layout("canonical")
    vendor_b = load_layout("vendorB")
    out = map_records(records, canonical, vendor_b)
    back = map_records(out, vendor_b, canonical)
    assert back == records


def test_map_vendor_to_vendor(records):
    canonical = load_layout("canonical")
    vendor_a = load_layout("vendorA")
    vendor_b = load_layout("vendorB")
    as_a = map_records(records, canonical, vendor_a)
    as_b = map_records(as_a, vendor_a, vendor_b)
    direct_b = map_records(records, canonical, vendor_b)
    assert as_b == direct_b


def test_map_with_custom_profile(records):
    canonical = load_layout("canonical")
    vendor_c = load_profile(EXAMPLES / "custom_profile.json")
    mapped = map_record(records[0], canonical, vendor_c)
    assert mapped["ID"] == "C-1001"
    assert mapped["Role"] == "Backend Engineer"


# --- validation -------------------------------------------------------------

def test_validate_examples_pass(records):
    problems = validate_records(records)
    assert problems == []


def test_validate_missing_required_field():
    bad = [{"first_name": "Ada", "last_name": "L", "email": "a@b.com"}]
    problems = validate_records(bad)
    assert any("candidate_id" in p for p in problems)


def test_validate_bad_email():
    bad = [{"candidate_id": "1", "first_name": "A", "last_name": "B",
            "email": "not-an-email"}]
    problems = validate_records(bad)
    assert any("email" in p for p in problems)


def test_validate_bad_date():
    bad = [{"candidate_id": "1", "first_name": "A", "last_name": "B",
            "email": "a@b.com", "applied_date": "2026-13-40"}]
    problems = validate_records(bad)
    assert any("applied_date" in p for p in problems)


def test_validate_bad_integer():
    bad = [{"candidate_id": "1", "first_name": "A", "last_name": "B",
            "email": "a@b.com", "years_experience": "seven"}]
    problems = validate_records(bad)
    assert any("years_experience" in p for p in problems)


# --- normalization ----------------------------------------------------------

def test_normalize_name():
    assert normalize_name("  alan  turing ") == "Alan Turing"
    assert normalize_name("TURING") == "Turing"
    assert normalize_name("mary-jane") == "Mary-Jane"


def test_normalize_email():
    assert normalize_email("Ada.Lovelace@Example.com") == "ada.lovelace@example.com"


def test_normalize_phone():
    assert normalize_phone("+1 (415) 555-0147") == "+14155550147"
    assert normalize_phone("415-555-0182") == "4155550182"


def test_normalize_date_forms():
    assert normalize_date("03/22/2026") == "2026-03-22"
    assert normalize_date("Mar 5, 2026") == "2026-03-05"
    assert normalize_date("5 Jan 2026") == "2026-01-05"
    assert normalize_date("2026-03-14") == "2026-03-14"
    # unparseable forms are left untouched
    assert normalize_date("sometime") == "sometime"


def test_normalize_record_full(records):
    out = normalize_record(records[2])
    assert out["first_name"] == "Alan Turing"
    assert out["last_name"] == "Turing"
    assert out["applied_date"] == "2026-03-05"


def test_normalize_then_validate_fixes_dates():
    raw = [{"candidate_id": "1", "first_name": "a", "last_name": "b",
            "email": "A@B.COM", "applied_date": "03/22/2026"}]
    assert validate_records(normalize_records(raw)) == []


# --- export -----------------------------------------------------------------

def test_export_json_round_trip(records):
    text = to_json(records)
    assert json.loads(text) == records


def test_export_csv_header_and_rows(records):
    text = to_csv(records)
    lines = text.strip().splitlines()
    assert lines[0].startswith("candidate_id,")
    assert len(lines) == len(records) + 1
    assert "C-1001" in lines[1]


def test_export_csv_union_of_keys():
    recs = [{"a": 1}, {"b": 2}]
    text = to_csv(recs)
    header = text.splitlines()[0]
    assert "a" in header and "b" in header


def test_write_export_file(tmp_path, records):
    from atslens.exporter import write_export
    out = tmp_path / "out.csv"
    write_export(records, "csv", str(out))
    assert out.exists()
    assert "candidate_id" in out.read_text(encoding="utf-8")


# --- diff --------------------------------------------------------------------

def test_diff_identical_is_clean(records):
    report = compute_diff(records, records)
    assert diff_is_clean(report)
    assert report["summary"]["changed"] == 0
    assert report["summary"]["unchanged"] == len(records)


def test_diff_detects_added_and_removed():
    before = [{"candidate_id": "1", "email": "a@b.com"}]
    after = [{"candidate_id": "2", "email": "c@d.com"}]
    report = compute_diff(before, after)
    assert report["added"] == ["2"]
    assert report["removed"] == ["1"]
    assert not diff_is_clean(report)


def test_diff_detects_field_change_and_removal():
    before = [{"candidate_id": "1", "status": "screen", "phone": "+15550001"}]
    after = [{"candidate_id": "1", "status": "onsite"}]
    report = compute_diff(before, after)
    changed = report["changed"]["1"]
    assert changed["status"] == {"before": "screen", "after": "onsite"}
    assert changed["phone"] == {"before": "+15550001", "after": None}


def test_diff_record_added_field():
    changes = diff_record({"a": 1}, {"a": 1, "b": 2})
    assert changes == {"b": {"before": None, "after": 2}}


def test_diff_custom_key():
    before = [{"ref": "X", "v": 1}]
    after = [{"ref": "X", "v": 2}]
    report = compute_diff(before, after, key="ref")
    assert report["key"] == "ref"
    assert report["changed"]["X"]["v"] == {"before": 1, "after": 2}


def test_diff_unkeyed_records_surface():
    before = [{"candidate_id": "", "email": "a@b.com"}]
    after = []
    report = compute_diff(before, after)
    # an unkeyed 'before' record still shows up as removed
    assert report["summary"]["removed"] == 1


# --- CLI --------------------------------------------------------------------

def test_cli_validate_pass(capsys):
    rc = main(["validate", str(EXAMPLES / "records.json")])
    assert rc == 0
    assert "VALID" in capsys.readouterr().out


def test_cli_validate_fail(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"first_name": "A"}]), encoding="utf-8")
    rc = main(["validate", str(bad)])
    assert rc == 1


def test_cli_map(capsys):
    rc = main(["map", str(EXAMPLES / "records.json"), "--to", "vendorA"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert "applicantId" in out[0]


def test_cli_export_json(capsys):
    rc = main(["export", str(EXAMPLES / "records.json"), "--format", "json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)[0]["candidate_id"] == "C-1001"


def test_cli_layouts(capsys):
    rc = main(["layouts"])
    assert rc == 0
    assert "vendorA" in capsys.readouterr().out


def test_cli_diff_clean(tmp_path, records, capsys):
    p = tmp_path / "recs.json"
    p.write_text(json.dumps(records), encoding="utf-8")
    rc = main(["diff", str(p), str(p)])
    assert rc == 0
    assert "CLEAN" in capsys.readouterr().out


def test_cli_diff_differences(tmp_path, records, capsys):
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(records), encoding="utf-8")
    changed = json.loads(json.dumps(records))
    changed[0]["status"] = "hired"
    after.write_text(json.dumps(changed), encoding="utf-8")
    rc = main(["diff", str(before), str(after), "--json"])
    assert rc == 1
    report = json.loads(capsys.readouterr().out)
    assert report["summary"]["changed"] == 1


def test_cli_diff_with_from_after_layout(tmp_path, records, capsys):
    """A vendorB export diffs clean against a canonical baseline when
    translated back through --from-after."""
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text(json.dumps(records), encoding="utf-8")
    vendor_b = map_records(records, load_layout("canonical"),
                           load_layout("vendorB"))
    after.write_text(json.dumps(vendor_b), encoding="utf-8")
    rc = main(["diff", str(before), str(after), "--from-after", "vendorB"])
    assert rc == 0
    assert "CLEAN" in capsys.readouterr().out
