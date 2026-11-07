#!/usr/bin/env python3
"""
csv-cleaner: Remove duplicate rows and trim whitespace in CSV files.

Usage:
    csv-cleaner [options] file1 [file2 ...]
Options:
    -o OUTPUT, --output=OUTPUT   Write cleaned data to OUTPUT (default: overwrite input file)
    -s, --skip-headers          Preserve the first row as header (do not dedupe it)
    -h, --help                  Show this help message and exit
"""

import csv
import sys
import argparse
from pathlib import Path
from typing import Iterable, Tuple, Set


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove duplicate rows and trim whitespace in CSV files.",
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("files", nargs="+", help="Input CSV files")
    parser.add_argument(
        "-o", "--output", help="Output file or directory; if omitted, overwrite input"
    )
    parser.add_argument(
        "-s",
        "--skip-headers",
        action="store_true",
        help="Preserve the first row as header (do not dedupe it)",
    )
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message")
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        sys.exit(0)
    return args


def trim_row(row: Iterable[str]) -> Tuple[str, ...]:
    return tuple(cell.strip() for cell in row)


def dedupe_rows(rows: Iterable[Tuple[str, ...]]) -> Iterable[Tuple[str, ...]]:
    seen: Set[Tuple[str, ...]] = set()
    for row in rows:
        if row not in seen:
            seen.add(row)
            yield row


def process_file(
    path: Path, output: Path | None, skip_headers: bool
) -> None:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return

    header = rows[0] if skip_headers else None
    data_rows = rows[1:] if skip_headers else rows

    cleaned = [trim_row(row) for row in data_rows]
    cleaned = list(dedupe_rows(cleaned))

    if header:
        cleaned.insert(0, trim_row(header))

    out_path = output or path
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(cleaned)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output) if args.output else None

    for file in args.files:
        src = Path(file)
        if not src.is_file():
            print(f"Error: {src} is not a file", file=sys.stderr)
            continue

        if output_dir:
            if output_dir.is_dir():
                dst = output_dir / src.name
            else:
                dst = output_dir
        else:
            dst = None

        try:
            process_file(src, dst, args.skip_headers)
            print(f"Processed {src} → {dst or src}")
        except Exception as e:
            print(f"Failed {src}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
