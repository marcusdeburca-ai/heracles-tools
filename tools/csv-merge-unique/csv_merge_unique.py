#!/usr/bin/env python3
"""
csv-merge-unique: Merge several CSV files that share the same header,
remove duplicate rows, and write the result to stdout or a file.

Features
--------
* Validates that all input files have identical headers (order matters).
* Streams input files line‑by‑line, keeping memory usage low.
* Uses a set of hashable tuples to detect duplicate rows.
* Supports custom delimiter, quoting style and output destination.
* Provides a helpful ``--help`` message.

Limitations
-----------
* Only works with text CSV files (no binary data).
* Duplicate detection is based on exact field values; whitespace differences count.
* All files must fit the same column order; differing headers cause an error.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, List, Tuple, Set


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Merge CSV files with identical headers, removing duplicate rows.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="CSV files to merge (at least one).",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write result to FILE instead of stdout.",
    )
    p.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help="Field delimiter character.",
    )
    p.add_argument(
        "-q",
        "--quotechar",
        default='"',
        help="Character used to quote fields.",
    )
    p.add_argument(
        "--skip-empty",
        action="store_true",
        help="Skip completely empty rows (all fields empty).",
    )
    return p.parse_args()


def read_header(path: Path, **csv_opts) -> List[str]:
    with path.open(newline="") as f:
        reader = csv.reader(f, **csv_opts)
        try:
            return next(reader)
        except StopIteration:
            raise ValueError(f"File '{path}' is empty.")


def iter_rows(path: Path, **csv_opts) -> Iterable[Tuple[str, ...]]:
    with path.open(newline="") as f:
        reader = csv.reader(f, **csv_opts)
        # skip header
        next(reader, None)
        for row in reader:
            yield tuple(row)


def main() -> int:
    args = parse_args()
    csv_opts = {"delimiter": args.delimiter, "quotechar": args.quotechar}
    # Validate headers
    expected_header = read_header(args.files[0], **csv_opts)
    for p in args.files[1:]:
        hdr = read_header(p, **csv_opts)
        if hdr != expected_header:
            sys.stderr.write(
                f"Header mismatch: {args.files[0]} has {expected_header}, but {p} has {hdr}\n"
            )
            return 1

    seen: Set[Tuple[str, ...]] = set()
    out_f = args.output.open("w", newline="") if args.output else sys.stdout
    writer = csv.writer(out_f, **csv_opts)
    writer.writerow(expected_header)

    for path in args.files:
        for row in iter_rows(path, **csv_opts):
            if args.skip_empty and all(cell == "" for cell in row):
                continue
            if row not in seen:
                seen.add(row)
                writer.writerow(row)

    if args.output:
        out_f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
