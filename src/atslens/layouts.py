"""Field layouts (mapping profiles) for known vendor schemas.

A *layout* maps canonical field names to a vendor's field names. The
canonical layout is the identity map. Vendor layouts are authored here as
generic, original examples; users can supply their own with --profile.

Profile JSON format::

    {
      "name": "vendorX",
      "description": "...",
      "fields": { "<canonical_field>": "<vendor_field>", ... }
    }

Only canonical fields that appear in "fields" are remapped; any canonical
field absent from a layout keeps its canonical name.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

from .schema import CANONICAL_SCHEMA


@dataclass
class Layout:
    """A named mapping between canonical field names and vendor field names."""

    name: str
    description: str
    # canonical_field -> vendor_field
    fields: dict[str, str] = dc_field(default_factory=dict)

    def to_vendor_key(self, canonical_field: str) -> str:
        return self.fields.get(canonical_field, canonical_field)

    def to_canonical_key(self, vendor_field: str) -> str:
        for canonical, vendor in self.fields.items():
            if vendor == vendor_field:
                return canonical
        return vendor_field

    def vendor_fields(self) -> list[str]:
        """Ordered vendor field names following canonical schema order."""
        return [self.to_vendor_key(c) for c in CANONICAL_SCHEMA]


# --- built-in layouts -------------------------------------------------------

# Canonical layout: identity map (every field keeps its canonical name).
_CANONICAL = Layout(
    name="canonical",
    description="Neutral vendor-independent schema (identity mapping).",
    fields={c: c for c in CANONICAL_SCHEMA},
)

# vendorA: a flat camelCase-ish layout typical of REST-first ATS products.
_VENDOR_A = Layout(
    name="vendorA",
    description="Generic camelCase REST layout (authored example).",
    fields={
        "candidate_id": "applicantId",
        "first_name": "givenName",
        "last_name": "familyName",
        "email": "emailAddress",
        "phone": "phoneNumber",
        "applied_date": "applicationDate",
        "job_title": "positionTitle",
        "location": "city",
        "years_experience": "yearsExp",
        "source": "leadSource",
        "status": "pipelineStage",
    },
)

# vendorB: a verbose snake_case layout typical of HR-suite exports.
_VENDOR_B = Layout(
    name="vendorB",
    description="Generic snake_case HR-suite layout (authored example).",
    fields={
        "candidate_id": "cand_ref",
        "first_name": "fname",
        "last_name": "lname",
        "email": "email_addr",
        "phone": "contact_phone",
        "applied_date": "date_applied",
        "job_title": "req_title",
        "location": "geo",
        "years_experience": "experience_years",
        "source": "channel",
        "status": "stage",
    },
)

BUILTIN_LAYOUTS: dict[str, Layout] = {
    layout.name: layout
    for layout in (_CANONICAL, _VENDOR_A, _VENDOR_B)
}


def list_layouts() -> list[Layout]:
    """Return built-in layouts in a stable order."""
    return list(BUILTIN_LAYOUTS.values())


def load_layout(name: str) -> Layout:
    """Load a built-in layout by name."""
    try:
        return BUILTIN_LAYOUTS[name]
    except KeyError:
        known = ", ".join(BUILTIN_LAYOUTS)
        raise KeyError(f"unknown layout '{name}' (known: {known})") from None


def load_profile(path: str | Path) -> Layout:
    """Load a custom layout from a JSON profile file."""
    path = Path(path)
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if "fields" not in data or not isinstance(data["fields"], dict):
        raise ValueError(f"profile '{path}' must contain a 'fields' object")
    return Layout(
        name=str(data.get("name", path.stem)),
        description=str(data.get("description", "")),
        fields={str(k): str(v) for k, v in data["fields"].items()},
    )


def resolve_layout(name_or_path: str) -> Layout:
    """Resolve a layout from a built-in name or, failing that, a profile file."""
    if name_or_path in BUILTIN_LAYOUTS:
        return BUILTIN_LAYOUTS[name_or_path]
    candidate = Path(name_or_path)
    if candidate.exists():
        return load_profile(candidate)
    raise KeyError(
        f"unknown layout or missing profile file: '{name_or_path}'"
    )
