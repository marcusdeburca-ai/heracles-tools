#!/usr/bin/env python3
"""csv-grep: filter CSV rows by regular expressions applied to named columns.

Reads one or more CSV files, never modifies them, and writes matching rows
(plus a single header line) to stdout. Standard library only, no network.
"""
import argparse
import csv
import re
import sys

EPILOG = """\
examples:
  csv-grep -c status=^(failed|error)$ jobs.csv
  csv-grep -c email=@example\\.com$ -c plan=pro users.csv
  csv-grep --any -c city=paris -c city=berlin -i people.csv
  csv-grep -v -c note=^$ data.csv            # rows where 'note' is NOT empty
  csv-grep --count -c 3=^2024 -d ';' export.csv   # column 3 by 1-based number

exit codes: 0 = at least one row matched, 1 = no rows matched, 2 = error.
"""


def parse_cond(text):
    if "=" not in text:
        raise argparse.ArgumentTypeError(
            "condition must look like COLUMN=REGEX, got %r" % text)
    col, pat = text.split("=", 1)
    if not col:
        raise argparse.ArgumentTypeError("empty column name in %r" % text)
    return col, pat


def build_parser():
    p = argparse.ArgumentParser(
        prog="csv-grep",
        description="Print CSV rows whose columns match regular expressions. "
                    "Input files are only read, never modified.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", metavar="FILE", help="CSV file(s) to search")
    p.add_argument("-c", "--cond", action="append", required=True, type=parse_cond,
                   metavar="COLUMN=REGEX",
                   help="condition; COLUMN is a header name or a 1-based number. "
                        "Repeatable. The regex uses re.search (unanchored).")
    p.add_argument("--any", action="store_true",
                   help="match if ANY condition matches (default: ALL must match)")
    p.add_argument("-v", "--invert", action="store_true",
                   help="print rows that do NOT match")
    p.add_argument("-i", "--ignore-case", action="store_true",
                   help="case-insensitive matching")
    p.add_argument("-d", "--delimiter", default=",",
                   help="field delimiter (default: ','; use '\\t' for tabs)")
    p.add_argument("--count", action="store_true",
                   help="print only the number of matching rows")
    return p


def resolve(col, header):
    """Return the 0-based index for a header name or 1-based number."""
    if col in header:
        return header.index(col)
    if col.isdigit() and 1 <= int(col) <= len(header):
        return int(col) - 1
    return None


def main(argv=None):
    args = build_parser().parse_args(argv)
    delim = "\t" if args.delimiter == "\\t" else args.delimiter
    if len(delim) != 1:
        print("csv-grep: delimiter must be a single character", file=sys.stderr)
        return 2

    flags = re.IGNORECASE if args.ignore_case else 0
    compiled = []
    for col, pat in args.cond:
        try:
            compiled.append((col, re.compile(pat, flags)))
        except re.error as exc:
            print("csv-grep: bad regex %r: %s" % (pat, exc), file=sys.stderr)
            return 2

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    writer = csv.writer(sys.stdout, delimiter=delim, lineterminator="\n")

    out_header = None
    total = 0
    errors = False
    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

    for path in args.files:
        try:
            fh = open(path, newline="", encoding="utf-8-sig")
        except OSError as exc:
            print("csv-grep: cannot open %s: %s" % (path, exc), file=sys.stderr)
            errors = True
            continue
        with fh:
            try:
                reader = csv.reader(fh, delimiter=delim)
                header = next(reader, None)
                if header is None:
                    continue
                targets = []
                for col, rx in compiled:
                    idx = resolve(col, header)
                    if idx is None:
                        print("csv-grep: %s: no column %r" % (path, col),
                              file=sys.stderr)
                        break
                    targets.append((idx, rx))
                else:
                    if out_header is None:
                        out_header = header
                        if not args.count:
                            writer.writerow(header)
                    elif header != out_header:
                        print("csv-grep: %s: header differs from first file, skipped"
                              % path, file=sys.stderr)
                        errors = True
                        continue
                    combine = any if args.any else all
                    for row in reader:
                        hits = (rx.search(row[i] if i < len(row) else "")
                                for i, rx in targets)
                        matched = combine(bool(h) for h in hits)
                        if matched != args.invert:
                            total += 1
                            if not args.count:
                                writer.writerow(row)
                    continue
                errors = True  # reached only via the 'break' (missing column)
            except (csv.Error, UnicodeDecodeError) as exc:
                print("csv-grep: %s: %s" % (path, exc), file=sys.stderr)
                errors = True

    if args.count:
        print(total)
    if errors:
        return 2
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
