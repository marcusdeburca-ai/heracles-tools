#!/usr/bin/env python3
"""csv-dedupe-lint: report duplicate rows, blank cells, and ragged rows in CSV files.

Reads only the files you pass in. Never touches the network. Never deletes files.
Optionally writes a deduplicated copy to a NEW path you specify.
"""
import argparse
import csv
import sys
from collections import Counter


def lint_file(path, key_columns, delimiter):
    problems = []
    seen = Counter()
    header = None
    expected_cols = None
    dup_rows = 0
    blank_cells = 0
    ragged_rows = 0
    total_rows = 0
    unique_rows = []

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh, delimiter=delimiter)
        for lineno, row in enumerate(reader, start=1):
            if not row or all(not c.strip() for c in row):
                continue
            if header is None:
                header = row
                expected_cols = len(row)
                continue
            total_rows += 1
            if len(row) != expected_cols:
                ragged_rows += 1
                problems.append(f"line {lineno}: expected {expected_cols} columns, got {len(row)}")
            blanks = sum(1 for c in row if not c.strip())
            if blanks:
                blank_cells += blanks
                problems.append(f"line {lineno}: {blanks} blank cell(s)")

            if key_columns:
                try:
                    key = tuple(row[header.index(k)] for k in key_columns)
                except (ValueError, IndexError):
                    key = tuple(row)
            else:
                key = tuple(row)

            seen[key] += 1
            if seen[key] > 1:
                dup_rows += 1
                problems.append(f"line {lineno}: duplicate of an earlier row (key={key})")
            else:
                unique_rows.append(row)

    return {
        "path": path,
        "header": header or [],
        "total_rows": total_rows,
        "duplicates": dup_rows,
        "blank_cells": blank_cells,
        "ragged_rows": ragged_rows,
        "problems": problems,
        "unique_rows": unique_rows,
    }


def write_clean(result, out_path, delimiter):
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter=delimiter)
        if result["header"]:
            writer.writerow(result["header"])
        writer.writerows(result["unique_rows"])


def build_parser():
    p = argparse.ArgumentParser(
        prog="csv-dedupe-lint",
        description=(
            "Lint CSV files for duplicate rows, blank cells, and ragged rows. "
            "The first non-empty row of each file is treated as the header."
        ),
        epilog=(
            "Examples:\n"
            "  csv-dedupe-lint data.csv\n"
            "  csv-dedupe-lint --key id,email a.csv b.csv\n"
            "  csv-dedupe-lint --write-clean cleaned.csv data.csv\n"
            "Exit status: 0 if no problems found, 1 if problems found, 2 on usage error."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", help="CSV file(s) to lint")
    p.add_argument("--key", default="",
                   help="comma-separated column names that define a duplicate (default: whole row)")
    p.add_argument("--delimiter", default=",", help="field delimiter (default: ',')")
    p.add_argument("--write-clean", metavar="OUT",
                   help="write a deduplicated copy to OUT (only valid with one input file; "
                        "OUT must not already exist)")
    p.add_argument("--max-report", type=int, default=20,
                   help="max problem lines to print per file (default: 20)")
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.write_clean and len(args.files) != 1:
        parser.error("--write-clean requires exactly one input file")
    if args.write_clean:
        import os
        if os.path.exists(args.write_clean):
            parser.error(f"refusing to overwrite existing file: {args.write_clean}")
    if len(args.delimiter) != 1:
        parser.error("--delimiter must be a single character")

    key_columns = [k.strip() for k in args.key.split(",") if k.strip()]
    any_problems = False

    for path in args.files:
        try:
            result = lint_file(path, key_columns, args.delimiter)
        except FileNotFoundError:
            print(f"{path}: file not found", file=sys.stderr)
            any_problems = True
            continue
        except (UnicodeDecodeError, csv.Error) as exc:
            print(f"{path}: could not parse as CSV ({exc})", file=sys.stderr)
            any_problems = True
            continue

        print(f"== {path}")
        print(f"   rows: {result['total_rows']}  duplicates: {result['duplicates']}  "
              f"blank cells: {result['blank_cells']}  ragged rows: {result['ragged_rows']}")
        for line in result["problems"][: args.max_report]:
            print(f"   - {line}")
        hidden = len(result["problems"]) - args.max_report
        if hidden > 0:
            print(f"   ... and {hidden} more (raise --max-report to see them)")
        if result["problems"]:
            any_problems = True

        if args.write_clean:
            write_clean(result, args.write_clean, args.delimiter)
            print(f"   wrote deduplicated copy to {args.write_clean}")

    return 1 if any_problems else 0


if __name__ == "__main__":
    sys.exit(main())
