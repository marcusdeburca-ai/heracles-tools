#!/usr/bin/env python3
"""
csv-unique-rows: Remove duplicate rows from CSV files while preserving order.

Usage:
  csv-unique-rows [options] <input.csv> [<output.csv>]

Options:
  -h, --help        Show this help message and exit.
  -c, --columns COL1,COL2,...
                     Comma‑separated list of column names or indices to consider for uniqueness.
                     If omitted, the entire row is used.
  -d, --delimiter CHAR
                     Field delimiter (default: ',').
  -e, --encoding ENC
                     File encoding (default: 'utf-8').

The script reads the input CSV, removes duplicate rows based on the specified columns,
and writes the result to the output file (or stdout if not specified).
It never modifies the input file and never accesses the network.
"""

import argparse
import csv
import sys
from typing import List, Tuple, Set, Iterable


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove duplicate rows from CSV files while preserving order."
    )
    parser.add_argument(
        "input",
        help="Path to the input CSV file.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="-",
        help="Path to the output CSV file (default: stdout).",
    )
    parser.add_argument(
        "-c",
        "--columns",
        help="Comma‑separated list of column names or 0‑based indices to determine uniqueness.",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        default=",",
        help="Field delimiter (default: ',').",
    )
    parser.add_argument(
        "-e",
        "--encoding",
        default="utf-8",
        help="File encoding (default: 'utf-8').",
    )
    return parser.parse_args(argv)


def get_column_indices(
    header: List[str], cols: str, delimiter: str
) -> List[int]:
    """Return list of column indices from header or indices string."""
    if cols is None:
        return list(range(len(header)))
    indices: List[int] = []
    for part in cols.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part)
            if idx < 0 or idx >= len(header):
                raise ValueError(f"Column index {idx} out of range.")
            indices.append(idx)
        else:
            if part not in header:
                raise ValueError(f"Column name '{part}' not found in header.")
            indices.append(header.index(part))
    return indices


def unique_rows(
    rows: Iterable[List[str]], key_indices: List[int]
) -> Iterable[List[str]]:
    seen: Set[Tuple[str, ...]] = set()
    for row in rows:
        key = tuple(row[i] for i in key_indices)
        if key not in seen:
            seen.add(key)
            yield row


def main(argv: List[str] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    try:
        with open(args.input, newline="", encoding=args.encoding) as inf:
            reader = csv.reader(inf, delimiter=args.delimiter)
            header = next(reader)
            col_indices = get_column_indices(header, args.columns, args.delimiter)
            rows = list(reader)

        unique = list(unique_rows(rows, col_indices))

        out_file = None if args.output == "-" else args.output
        with (open(out_file, "w", newline="", encoding=args.encoding)
              if out_file else sys.stdout) as outf:
            writer = csv.writer(outf, delimiter=args.delimiter)
            writer.writerow(header)
            writer.writerows(unique)

    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
