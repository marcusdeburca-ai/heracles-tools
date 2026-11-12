#!/usr/bin/env python3
"""
csv-schema-check: Validate CSV files against a JSON schema.

The schema is a JSON object mapping column names to expected types:
    "int", "float", "bool", "str", "date" (ISO 8601).

Example:
{
    "id": "int",
    "price": "float",
    "active": "bool",
    "name": "str",
    "created": "date"
}
"""

import argparse
import csv
import json
import sys
import datetime
from pathlib import Path
from typing import Callable, Dict, List, Tuple

TYPE_PARSERS: Dict[str, Callable[[str], bool]] = {
    "int": lambda v: int(v) is not None,
    "float": lambda v: float(v) is not None,
    "bool": lambda v: v.lower() in {"true", "false", "1", "0"},
    "str": lambda v: True,
    "date": lambda v: datetime.datetime.fromisoformat(v) is not None,
}


def load_schema(path: Path) -> Dict[str, str]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Schema JSON must be an object mapping column names to types.")
        for col, typ in data.items():
            if typ not in TYPE_PARSERS:
                raise ValueError(f"Unsupported type '{typ}' for column '{col}'.")
        return data
    except Exception as e:
        sys.stderr.write(f"Error loading schema: {e}\n")
        sys.exit(2)


def validate_row(row: Dict[str, str], schema: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """Return list of (column, value, expected_type) for mismatches."""
    errors = []
    for col, typ in schema.items():
        val = row.get(col, "")
        if val == "":
            # empty string counts as missing – treat as error
            errors.append((col, val, typ))
            continue
        try:
            if not TYPE_PARSERS[typ](val):
                errors.append((col, val, typ))
        except Exception:
            errors.append((col, val, typ))
    return errors


def process_file(csv_path: Path, schema: Dict[str, str]) -> int:
    """Validate CSV file; return number of error rows."""
    error_rows = 0
    try:
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            missing = set(schema) - set(reader.fieldnames or [])
            if missing:
                sys.stderr.write(f"{csv_path}: missing columns in CSV: {', '.join(missing)}\n")
                return 1
            for i, row in enumerate(reader, start=2):  # header is line 1
                errs = validate_row(row, schema)
                if errs:
                    error_rows += 1
                    for col, val, typ in errs:
                        sys.stdout.write(
                            f"{csv_path}:{i}: column '{col}' value '{val}' not {typ}\n"
                        )
    except Exception as e:
        sys.stderr.write(f"Failed to read {csv_path}: {e}\n")
        return 1
    return error_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate CSV files against a JSON column‑type schema.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "schema",
        type=Path,
        help="Path to JSON schema file (column → type).",
    )
    parser.add_argument(
        "csv_files",
        nargs="+",
        type=Path,
        help="One or more CSV files to validate.",
    )
    args = parser.parse_args()

    schema = load_schema(args.schema)

    total_errors = 0
    for csv_path in args.csv_files:
        if not csv_path.is_file():
            sys.stderr.write(f"File not found: {csv_path}\n")
            continue
        total_errors += process_file(csv_path, schema)

    if total_errors:
        sys.exit(1)
    else:
        sys.stdout.write("All files passed validation.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
