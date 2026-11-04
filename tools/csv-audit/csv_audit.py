#!/usr/bin/env python3
"""csv-audit: find common problems in CSV files and optionally write a cleaned copy."""
import argparse
import csv
import os
import sys
from collections import Counter

EPILOG = """\
Checks performed:
  - duplicate or blank header names
  - blank rows
  - ragged rows (field count differs from the header)
  - cells with leading/trailing whitespace
  - exact duplicate rows (after whitespace stripping)
  - columns that are entirely empty

With --clean DIR, a cleaned copy named <name>.clean.csv is written into DIR:
whitespace stripped, blank and duplicate rows dropped, short rows padded,
rows with too many fields left out (and reported). Input files are never
modified, and existing files in DIR are never overwritten.

Exit status: 0 = no issues, 1 = issues found, 2 = a file could not be processed.
"""


def read_rows(path, encoding, delimiter):
    with open(path, newline="", encoding=encoding) as f:
        sample = f.read(8192)
        f.seek(0)
        if delimiter:
            dialect = type("D", (csv.excel,), {"delimiter": delimiter})
        else:
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
        reader = csv.reader(f, dialect)
        rows = [(reader.line_num, r) for r in reader]
    return rows, dialect


def analyze(rows):
    """Return (issues, header, cleaned_rows, data_row_count)."""
    issues = {}

    def note(kind, line):
        issues.setdefault(kind, []).append(line)

    header = [c.strip() for c in rows[0][1]]
    width = len(header)
    counts = Counter(h.lower() for h in header)
    for name, n in counts.items():
        if name == "":
            note("blank header name", 1)
        elif n > 1:
            note(f"duplicate header name '{name}'", 1)

    seen = set()
    filled = [0] * width
    cleaned = [header]
    data_rows = 0
    for line, row in rows[1:]:
        if not any(c.strip() for c in row):
            note("blank row", line)
            continue
        data_rows += 1
        if any(c != c.strip() for c in row):
            note("row with leading/trailing whitespace", line)
        if len(row) != width:
            note(f"ragged row (header has {width} fields)", line)
            if len(row) > width:
                continue
        padded = [c.strip() for c in row] + [""] * (width - len(row))
        key = tuple(padded)
        if key in seen:
            note("duplicate row", line)
            continue
        seen.add(key)
        for i, c in enumerate(padded):
            if c:
                filled[i] += 1
        cleaned.append(padded)
    if data_rows:
        for i, n in enumerate(filled):
            if n == 0:
                note(f"column '{header[i] or i + 1}' is entirely empty", 1)
    return issues, header, cleaned, data_rows


def write_clean(path, outdir, cleaned, delimiter):
    os.makedirs(outdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(outdir, stem + ".clean.csv")
    if os.path.exists(out):
        raise FileExistsError(f"refusing to overwrite existing file: {out}")
    with open(out, "x", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=delimiter, lineterminator="\n").writerows(cleaned)
    return out


def main():
    ap = argparse.ArgumentParser(
        prog="csv-audit",
        description="Audit CSV files for common structural and hygiene problems.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("files", nargs="+", help="CSV file(s) to audit")
    ap.add_argument("-d", "--delimiter", help="field delimiter (default: auto-detect)")
    ap.add_argument("-e", "--encoding", default="utf-8-sig",
                    help="input encoding (default: utf-8-sig, which also handles a BOM)")
    ap.add_argument("--clean", metavar="DIR",
                    help="write cleaned copies into DIR (never overwrites)")
    ap.add_argument("-n", "--max-examples", type=int, default=5,
                    help="max line numbers listed per issue (default: 5)")
    args = ap.parse_args()

    status = 0
    for path in args.files:
        try:
            rows, dialect = read_rows(path, args.encoding, args.delimiter)
            if not rows:
                print(f"{path}: file is empty")
                status = max(status, 1)
                continue
            issues, header, cleaned, data_rows = analyze(rows)
            print(f"{path}: {data_rows} data rows, {len(header)} columns, "
                  f"delimiter {dialect.delimiter!r}")
            if not issues:
                print("  no issues found")
            for kind, lines in issues.items():
                shown = ", ".join(map(str, lines[:args.max_examples]))
                more = f" (+{len(lines) - args.max_examples} more)" if len(lines) > args.max_examples else ""
                print(f"  {kind}: {len(lines)} - line(s) {shown}{more}")
            if issues:
                status = max(status, 1)
            if args.clean:
                out = write_clean(path, args.clean, cleaned, dialect.delimiter)
                print(f"  cleaned copy written: {out}")
        except (OSError, UnicodeDecodeError, csv.Error) as e:
            print(f"{path}: error: {e}", file=sys.stderr)
            status = 2
    return status


if __name__ == "__main__":
    sys.exit(main())
