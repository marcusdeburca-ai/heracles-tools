#!/usr/bin/env python3
"""csv-type-check: find cells whose type differs from the rest of their column."""
import argparse
import csv
import datetime
import re
import sys
from collections import Counter

INT_RE = re.compile(r"^[+-]?\d+$")
NUM_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
BOOLS = {"true", "false", "yes", "no"}


def classify(value):
    """Return (kind, label) for a non-empty cell. Kind groups int and float."""
    v = value.strip()
    if INT_RE.match(v):
        return "number", "int"
    if NUM_RE.match(v):
        return "number", "float"
    if v.lower() in BOOLS:
        return "bool", "bool"
    try:
        datetime.date.fromisoformat(v)
        return "date", "date"
    except ValueError:
        pass
    try:
        datetime.datetime.fromisoformat(v)
        return "datetime", "datetime"
    except ValueError:
        pass
    return "text", "text"


def rows(path, args):
    with open(path, newline="", encoding=args.encoding) as f:
        reader = csv.reader(f, delimiter=args.delimiter)
        for row in reader:
            if row:
                yield reader.line_num, row


def data_rows(path, args):
    gen = rows(path, args)
    if not args.no_header:
        next(gen, None)
    return gen


def short(value, n=40):
    value = value.strip()
    return value if len(value) <= n else value[: n - 3] + "..."


def check(path, args):
    """Print a report for one file; return the number of flagged columns."""
    first = next(rows(path, args), None)
    if first is None:
        print(f"{path}: empty file")
        return 0
    ncols = len(first[1])
    names = ([f"col{i + 1}" for i in range(ncols)] if args.no_header
             else [c.strip() or f"col{i + 1}" for i, c in enumerate(first[1])])

    kinds = [Counter() for _ in range(ncols)]
    subs = [Counter() for _ in range(ncols)]
    empty = [0] * ncols
    ragged = nrows = 0

    for _, row in data_rows(path, args):
        nrows += 1
        if len(row) != ncols:
            ragged += 1
        for i in range(min(ncols, len(row))):
            if not row[i].strip():
                empty[i] += 1
            else:
                k, label = classify(row[i])
                kinds[i][k] += 1
                subs[i][label] += 1

    print(f"{path}: {nrows} data rows, {ncols} columns")
    if ragged:
        print(f"  warning: {ragged} row(s) have a field count different from {ncols}")

    # Decide which columns are mostly one type with a few outliers.
    outlier_cols = {}
    flagged = 0
    summaries = []
    for i, name in enumerate(names):
        total = sum(kinds[i].values())
        if total == 0:
            summaries.append((name, "empty", empty[i], None))
            continue
        dom, count = kinds[i].most_common(1)[0]
        share = count / total
        label = dom
        if dom == "number":
            label = "float" if subs[i]["float"] else "int"
        summaries.append((name, label, empty[i], share))
        if share < 1:
            flagged += 1
            if share >= args.threshold:
                outlier_cols[i] = dom
            else:
                dist = ", ".join(f"{k}={n}" for k, n in kinds[i].most_common())
                summaries[-1] = (name, "mixed", empty[i], share, dist)

    for s in summaries:
        share = "" if s[3] is None else f" ({s[3]:.0%} consistent)"
        print(f"  {s[0]}: {s[1]}{share}, {s[2]} empty")
        if len(s) == 5:
            print(f"      no dominant type: {s[4]}")

    if outlier_cols:
        found = {i: [] for i in outlier_cols}
        extra = Counter()
        for line, row in data_rows(path, args):
            for i, dom in outlier_cols.items():
                if i < len(row) and row[i].strip():
                    k, label = classify(row[i])
                    if k != dom:
                        if len(found[i]) < args.max_report:
                            found[i].append((line, label, row[i]))
                        else:
                            extra[i] += 1
        for i, items in found.items():
            print(f"  outliers in '{names[i]}' (expected {outlier_cols[i]}):")
            for line, label, val in items:
                print(f"    line {line}: {short(val)!r} looks like {label}")
            if extra[i]:
                print(f"    ... and {extra[i]} more")
    return flagged


def main():
    p = argparse.ArgumentParser(
        description="Infer the type of each CSV column and report cells that "
                    "don't match the column's dominant type. Types: int, float, "
                    "bool (true/false/yes/no), date (ISO), datetime (ISO), text. "
                    "Empty cells are counted but never treated as outliers. "
                    "Files are only read, never modified.",
        epilog="Exit status: 0 = all columns consistent, 1 = inconsistencies "
               "found, 2 = a file could not be read.")
    p.add_argument("files", nargs="+", help="CSV file(s) to check")
    p.add_argument("-d", "--delimiter", default=",", help="field delimiter (default ',')")
    p.add_argument("-e", "--encoding", default="utf-8-sig", help="file encoding (default utf-8-sig)")
    p.add_argument("--no-header", action="store_true", help="first row is data, not a header")
    p.add_argument("-t", "--threshold", type=float, default=0.9,
                   help="min share of non-empty cells a type needs to count as "
                        "dominant; below it the column is reported as 'mixed' (default 0.9)")
    p.add_argument("-m", "--max-report", type=int, default=10,
                   help="max outlier cells listed per column (default 10)")
    args = p.parse_args()
    if len(args.delimiter) != 1:
        p.error("--delimiter must be a single character")
    if not 0 < args.threshold <= 1:
        p.error("--threshold must be in (0, 1]")

    status = 0
    for path in args.files:
        try:
            if check(path, args):
                status = max(status, 1)
        except (OSError, UnicodeDecodeError, csv.Error) as exc:
            print(f"{path}: error: {exc}", file=sys.stderr)
            status = 2
    return status


if __name__ == "__main__":
    sys.exit(main())
