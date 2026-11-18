#!/usr/bin/env python3
"""csv-col-stats: profile each column of one or more CSV files (read-only)."""
import argparse
import csv
import json
import statistics
import sys
from collections import Counter

DESCRIPTION = """\
Profile every column of a CSV file: how many cells are filled, how many
distinct values there are, the shortest/longest value, numeric min/max/mean/
median when the column is numeric, and the most common values.

Files are only read, never modified. No network access is used.
"""

EPILOG = """\
examples:
  csv-col-stats data.csv
  csv-col-stats --top 5 a.csv b.csv
  csv-col-stats --delimiter ';' --json export.csv > profile.json
  csv-col-stats --columns email,country users.csv
"""


def to_number(s):
    try:
        v = float(s.replace(",", "") if s.count(",") and "." in s else s)
    except ValueError:
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v


def profile(path, delimiter, encoding, top, wanted):
    with open(path, newline="", encoding=encoding) as f:
        if delimiter is None:
            sample = f.read(65536)
            f.seek(0)
            try:
                delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
            except csv.Error:
                delimiter = ","
        reader = csv.reader(f, delimiter=delimiter)
        header = next(reader, None)
        if header is None:
            return {"file": path, "rows": 0, "columns": []}
        n = len(header)
        counters = [Counter() for _ in range(n)]
        nums = [[] for _ in range(n)]
        nonnum = [0] * n
        minlen = [None] * n
        maxlen = [0] * n
        rows = ragged = 0
        for row in reader:
            if not row:
                continue
            rows += 1
            if len(row) != n:
                ragged += 1
            for i in range(n):
                v = row[i].strip() if i < len(row) else ""
                if v == "":
                    continue
                counters[i][v] += 1
                L = len(v)
                minlen[i] = L if minlen[i] is None else min(minlen[i], L)
                maxlen[i] = max(maxlen[i], L)
                x = to_number(v)
                if x is None:
                    nonnum[i] += 1
                else:
                    nums[i].append(x)
    cols = []
    for i, name in enumerate(header):
        if wanted and name not in wanted:
            continue
        filled = sum(counters[i].values())
        info = {
            "name": name,
            "filled": filled,
            "empty": rows - filled,
            "unique": len(counters[i]),
            "min_len": minlen[i],
            "max_len": maxlen[i],
            "top": counters[i].most_common(top),
        }
        if filled and nonnum[i] == 0:
            xs = nums[i]
            info["numeric"] = {
                "min": min(xs),
                "max": max(xs),
                "mean": round(statistics.fmean(xs), 6),
                "median": statistics.median(xs),
            }
        cols.append(info)
    return {"file": path, "rows": rows, "ragged_rows": ragged, "columns": cols}


def print_text(res):
    print(f"== {res['file']}: {res['rows']} data rows, "
          f"{res.get('ragged_rows', 0)} ragged")
    for c in res["columns"]:
        total = c["filled"] + c["empty"]
        pct = 100.0 * c["filled"] / total if total else 0.0
        print(f"- {c['name']!r}: filled {c['filled']}/{total} ({pct:.1f}%), "
              f"unique {c['unique']}, length {c['min_len']}..{c['max_len']}")
        if "numeric" in c:
            n = c["numeric"]
            print(f"    numeric: min={n['min']} max={n['max']} "
                  f"mean={n['mean']} median={n['median']}")
        if c["top"]:
            tops = ", ".join(f"{v[:30]!r} x{k}" for v, k in c["top"])
            print(f"    top: {tops}")


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="csv-col-stats",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", help="CSV file(s) to profile")
    p.add_argument("-d", "--delimiter",
                   help="field delimiter (default: auto-detect among , ; tab |)")
    p.add_argument("-e", "--encoding", default="utf-8-sig",
                   help="file encoding (default: utf-8-sig, handles a BOM)")
    p.add_argument("-n", "--top", type=int, default=3,
                   help="number of most common values to show (default: 3)")
    p.add_argument("-c", "--columns",
                   help="comma-separated column names to include (default: all)")
    p.add_argument("--json", action="store_true", help="output JSON instead of text")
    args = p.parse_args(argv)

    wanted = set(args.columns.split(",")) if args.columns else None
    delim = "\t" if args.delimiter == "\\t" else args.delimiter
    if delim is not None and len(delim) != 1:
        p.error("--delimiter must be a single character (or \\t)")

    results, status = [], 0
    for path in args.files:
        try:
            results.append(profile(path, delim, args.encoding, max(args.top, 0), wanted))
        except (OSError, UnicodeDecodeError, csv.Error) as e:
            print(f"csv-col-stats: {path}: {e}", file=sys.stderr)
            status = 1
    if args.json:
        json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        for r in results:
            print_text(r)
    return status


if __name__ == "__main__":
    sys.exit(main())
