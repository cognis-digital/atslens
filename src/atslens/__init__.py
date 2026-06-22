"""atslens — ATS field-schema mapper & exporter for candidate-data portability.

A standard-library-only toolkit to map candidate records between a canonical
schema and named vendor field layouts, validate records, normalize fields,
and export to CSV/JSON. Built so candidate data can move between systems
without lock-in.

Maintainer: Cognis Digital
License: COCL 1.0
"""

__version__ = "0.1.0"

from .schema import CANONICAL_SCHEMA, ValidationError, validate_records
from .layouts import (
    BUILTIN_LAYOUTS,
    Layout,
    list_layouts,
    load_layout,
    load_profile,
)
from .mapper import map_records
from .normalize import normalize_record, normalize_records
from .exporter import to_csv, to_json
from .diff import compute_diff, diff_record, diff_is_clean

__all__ = [
    "__version__",
    "CANONICAL_SCHEMA",
    "ValidationError",
    "validate_records",
    "BUILTIN_LAYOUTS",
    "Layout",
    "list_layouts",
    "load_layout",
    "load_profile",
    "map_records",
    "normalize_record",
    "normalize_records",
    "to_csv",
    "to_json",
    "compute_diff",
    "diff_record",
    "diff_is_clean",
]
