#!/usr/bin/env python3
"""
csv-header-check: ensure every row in a CSV file matches the header columns.

Features
--------
* Detect rows with too few or too many fields.
* Optionally ignore empty trailing fields.
* Works with any delimiter (auto‑detected from the first line).
* Prints a concise report to stdout; non‑zero exit code on errors.

Usage
-----
    python csv-header-check.py [options] file1.csv [file2.csv ...]

Options
-------
    -h, --help          Show this help message and exit.
    -d, --delimiter D   Specify delimiter (default: auto‑detect from first line).
    -i, --ignore-trailing
                        Ignore extra empty fields at the end of a row.
    -q, --quiet         Suppress normal output, only print summary on stderr.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Tuple, Optional

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="csv-header-check",
        description="Validate that all rows in a CSV file have the same number of columns as the header.",
        add_help=False,
    )
    parser.add_argument("files", nargs="+", help="CSV file(s) to check")
    parser.add_argument("-d", "--delimiter", help="Field delimiter (default: auto-detect)")
    parser.add_argument("-i", "--ignore-trailing", action="store_true",
                        help="Ignore extra empty fields at the end of a row")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress per‑file reports; only print a summary to stderr")
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    return parser.parse_args(argv)

def detect_delimiter(sample: str) -> str:
    # Simple heuristic: try common delimiters and pick the one with most fields
    candidates = [",", "\t", ";", "|"]
    best = ","
    best_count = -1
    for d in candidates:
        count = sample.count(d)
        if count > best_count:
            best, best_count = d, count
    return best

def check_file(path: Path, delimiter: Optional[str], ignore_trailing: bool) -> Tuple[int, int]:
    """
    Returns (good_rows, bad_rows) counts.
    Prints details to stdout unless quiet mode is active.
    """
    good = bad = 0
    with path.open(newline='') as f:
        # Peek first line for delimiter detection if needed
        first = f.readline()
        if not first:
            print(f"{path}: empty file", file=sys.stderr)
            return 0, 0
        delim = delimiter or detect_delimiter(first)
        f.seek(0)  # rewind
        reader = csv.reader(f, delimiter=delim)
        try:
            header = next(reader)
        except StopIteration:
            print(f"{path}: no header line", file=sys.stderr)
            return 0, 0
        expected = len(header)
        for lineno, row in enumerate(reader, start=2):
            length = len(row)
            if ignore_trailing:
                # Trim trailing empty strings
                while length and row[-1] == "":
                    row.pop()
                    length -= 1
            if length == expected:
                good += 1
            else:
                bad += 1
                print(f"{path}:{lineno}: expected {expected} fields, got {length}")
    return good, bad

def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    total_good = total_bad = 0
    for filename in args.files:
        path = Path(filename)
        if not path.is_file():
            print(f"Error: {filename} is not a readable file", file=sys.stderr)
            continue
        good, bad = check_file(path, args.delimiter, args.ignore_trailing)
        total_good += good
        total_bad += bad
        if not args.quiet:
            print(f"{path}: {good} good rows, {bad} problematic rows")
    if total_bad:
        print(f"\nSummary: {total_bad} problematic rows across all files", file=sys.stderr)
        return 1
    else:
        print("\nAll checked rows match the header.", file=sys.stderr)
        return 0

if __name__ == "__main__":
    sys.exit(main())
