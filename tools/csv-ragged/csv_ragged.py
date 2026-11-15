#!/usr/bin/env python3
"""csv-ragged: report CSV rows whose column count differs from the header."""
import argparse
import collections
import csv
import sys

EPILOG = """\
examples:
  csv-ragged data.csv
  csv-ragged a.csv b.csv -d ';' --max-report 50
  csv-ragged data.csv --fix data.fixed.csv
  csv-ragged data.csv --fix data.fixed.csv --truncate

exit codes: 0 = all rows match header, 1 = ragged rows found, 2 = error.
Input files are only read. --fix writes a NEW file and refuses to overwrite.
"""


def sniff_delimiter(path, encoding):
    with open(path, newline="", encoding=encoding) as f:
        sample = f.read(65536)
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        return ","


def fix_row(row, width, truncate):
    if len(row) < width:
        return row + [""] * (width - len(row))
    if len(row) > width and truncate:
        return row[:width]
    return row


def process(path, args, out_writer):
    delim = args.delimiter or sniff_delimiter(path, args.encoding)
    counts = collections.Counter()
    bad = []
    blanks = 0
    width = None
    total = 0
    with open(path, newline="", encoding=args.encoding) as f:
        reader = csv.reader(f, delimiter=delim)
        for row in reader:
            if not row:
                blanks += 1
                continue
            if width is None:
                width = len(row)
                if out_writer:
                    out_writer.writerow(row)
                continue
            total += 1
            counts[len(row)] += 1
            if len(row) != width:
                bad.append((reader.line_num, len(row)))
            if out_writer:
                out_writer.writerow(fix_row(row, width, args.truncate))
    print(f"== {path} (delimiter {delim!r})")
    if width is None:
        print("  empty file: no header found")
        return 0
    print(f"  header columns: {width}; data rows: {total}; blank lines skipped: {blanks}")
    if not bad:
        print("  OK: every row matches the header")
        return 0
    short = sum(1 for _, n in bad if n < width)
    print(f"  RAGGED: {len(bad)} rows ({short} too short, {len(bad) - short} too long)")
    print("  field-count histogram: " + ", ".join(
        f"{n} fields x{c}" for n, c in sorted(counts.items())))
    for line, n in bad[:args.max_report]:
        print(f"  line {line}: {n} fields (expected {width})")
    if len(bad) > args.max_report:
        print(f"  ... {len(bad) - args.max_report} more (raise --max-report)")
    return len(bad)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="csv-ragged",
        description="Find CSV rows with a different number of fields than the header, "
                    "optionally writing a repaired copy (short rows padded).",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="CSV files to check")
    p.add_argument("-d", "--delimiter", help="field delimiter (default: auto-detect)")
    p.add_argument("-e", "--encoding", default="utf-8-sig",
                   help="input encoding (default: utf-8-sig)")
    p.add_argument("--max-report", type=int, default=20,
                   help="max bad rows listed per file (default: 20)")
    p.add_argument("--fix", metavar="OUT",
                   help="write a repaired copy to OUT (single input only; "
                        "OUT must not exist). Short rows are padded with empty fields.")
    p.add_argument("--truncate", action="store_true",
                   help="with --fix, also cut over-long rows down to header width "
                        "(this DISCARDS data in the extra fields)")
    args = p.parse_args(argv)

    if args.delimiter is not None and len(args.delimiter) != 1:
        p.error("--delimiter must be a single character")
    if args.fix and len(args.files) != 1:
        p.error("--fix works with exactly one input file")
    if args.truncate and not args.fix:
        p.error("--truncate only makes sense with --fix")
    if args.fix and args.fix in args.files:
        p.error("--fix output must differ from the input file")

    found = 0
    status = 0
    for path in args.files:
        out_f = None
        try:
            writer = None
            if args.fix:
                out_f = open(args.fix, "x", newline="", encoding="utf-8")
                writer = csv.writer(out_f, delimiter=args.delimiter or ",")
            found += process(path, args, writer)
            if args.fix:
                print(f"  wrote repaired copy: {args.fix}")
        except FileExistsError:
            print(f"error: {args.fix} already exists; refusing to overwrite",
                  file=sys.stderr)
            status = 2
        except (OSError, UnicodeDecodeError, csv.Error) as e:
            print(f"error: {path}: {e}", file=sys.stderr)
            status = 2
        finally:
            if out_f:
                out_f.close()
    if status:
        return status
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
