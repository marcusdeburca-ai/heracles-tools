#!/usr/bin/env python3
"""
csv-normalizer: a tiny CLI utility to clean and normalise CSV files.

Features
--------
* Strip leading/trailing whitespace from every field.
* Remove rows that are completely empty (all fields blank after stripping).
* Optionally enforce that every row has the same number of columns as the header.
* Write the cleaned CSV to stdout (or to a file via redirection).

The tool never writes to the input files and never performs any network I/O.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, List, TextIO


def _iter_rows(source: TextIO, dialect: str, delimiter: str) -> Iterable[List[str]]:
    """Yield rows from a CSV source using the requested dialect."""
    reader = csv.reader(source, dialect=dialect, delimiter=delimiter)
    for row in reader:
        yield row


def _clean_rows(
    rows: Iterable[List[str]],
    *,
    enforce_columns: bool,
    header: List[str] | None,
) -> List[List[str]]:
    """
    Return a cleaned list of rows.

    * Strip whitespace from each cell.
    * Drop rows that become completely empty.
    * If enforce_columns is True, drop rows whose column count differs from the header.
    """
    cleaned: List[List[str]] = []
    expected_len = len(header) if header else None

    for row in rows:
        stripped = [cell.strip() for cell in row]
        # Skip rows that are all empty after stripping
        if all(cell == "" for cell in stripped):
            continue

        if enforce_columns and expected_len is not None:
            if len(stripped) != expected_len:
                # skip mismatched rows
                continue

        cleaned.append(stripped)

    return cleaned


def process_file(
    path: Path,
    *,
    delimiter: str,
    dialect: str,
    enforce_columns: bool,
    output: TextIO,
) -> None:
    """Read *path*, clean it and write the result to *output*."""
    with path.open(newline="") as f:
        rows = list(_iter_rows(f, dialect=dialect, delimiter=delimiter))

    if not rows:
        return  # empty file

    header, *data = rows
    cleaned_data = _clean_rows(
        data,
        enforce_columns=enforce_columns,
        header=header,
    )
    # Write header + cleaned rows
    writer = csv.writer(output, dialect=dialect, delimiter=delimiter)
    writer.writerow([cell.strip() for cell in header])
    writer.writerows(cleaned_data)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="csv-normalizer",
        description="Clean and normalise CSV files: trim whitespace, drop empty rows, "
        "optionally enforce column count consistency.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Path(s) to CSV file(s) to process.",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help="Field delimiter character.",
    )
    parser.add_argument(
        "--dialect",
        default="excel",
        help="CSV dialect to use (as accepted by Python's csv module).",
    )
    parser.add_argument(
        "-e",
        "--enforce-columns",
        action="store_true",
        help="Drop rows whose column count differs from the header.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write combined output to this file (default: stdout).",
    )
    args = parser.parse_args(argv)

    out_handle: TextIO
    if args.output:
        out_handle = args.output.open("w", newline="")
    else:
        out_handle = sys.stdout

    try:
        for idx, file_path in enumerate(args.files):
            if not file_path.is_file():
                print(f"warning: {file_path} is not a file – skipping", file=sys.stderr)
                continue
            if idx > 0:
                # separate multiple inputs with a newline for readability
                out_handle.write("\n")
            process_file(
                file_path,
                delimiter=args.delimiter,
                dialect=args.dialect,
                enforce_columns=args.enforce_columns,
                output=out_handle,
            )
    finally:
        if args.output:
            out_handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
