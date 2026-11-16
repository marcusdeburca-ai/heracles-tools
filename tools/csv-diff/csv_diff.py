#!/usr/bin/env python3
"""csv-diff: compare two CSV files row by row using one or more key columns."""
import argparse
import csv
import json
import sys

EPILOG = """\
exit codes:
  0  files are equivalent (under the chosen options)
  1  differences found
  2  usage or input error

examples:
  csv-diff old.csv new.csv --key id
  csv-diff a.csv b.csv --key first,last --ignore updated_at
  csv-diff a.csv b.csv --key id --format json > diff.json
  csv-diff a.tsv b.tsv --key id --delimiter '\\t' --trim
"""


def die(msg):
    print(f"csv-diff: error: {msg}", file=sys.stderr)
    sys.exit(2)


def load(path, keys, delim, trim):
    """Return (header, {key_tuple: row_dict}, [(key, line_no)] duplicates)."""
    clean = (lambda s: (s or "").strip()) if trim else (lambda s: s or "")
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=delim)
            header = reader.fieldnames
            if not header:
                die(f"{path}: file is empty or has no header")
            missing = [k for k in keys if k not in header]
            if missing:
                die(f"{path}: key column(s) not found: {', '.join(missing)}")
            rows, dups = {}, []
            for row in reader:
                line = reader.line_num
                row = {h: clean(row.get(h)) for h in header}
                k = tuple(row[c] for c in keys)
                if k in rows:
                    dups.append((k, line))
                else:
                    rows[k] = row
    except OSError as e:
        die(f"cannot read {path}: {e.strerror or e}")
    except UnicodeDecodeError:
        die(f"{path}: not valid UTF-8")
    except csv.Error as e:
        die(f"{path}: CSV parse error: {e}")
    return header, rows, dups


def diff(old, new, keys, ignore):
    oh, orows, odups = old
    nh, nrows, ndups = new
    common = [h for h in oh if h in nh and h not in ignore]
    result = {
        "columns_removed": [h for h in oh if h not in nh],
        "columns_added": [h for h in nh if h not in oh],
        "removed": [k for k in orows if k not in nrows],
        "added": [k for k in nrows if k not in orows],
        "changed": [],
        "duplicate_keys_old": odups,
        "duplicate_keys_new": ndups,
    }
    for k, orow in orows.items():
        nrow = nrows.get(k)
        if nrow is None:
            continue
        cells = {c: [orow[c], nrow[c]] for c in common
                 if c not in keys and orow[c] != nrow[c]}
        if cells:
            result["changed"].append({"key": k, "cells": cells})
    result["unchanged"] = len(orows) - len(result["removed"]) - len(result["changed"])
    return result


def has_diff(r):
    return any(r[k] for k in ("columns_removed", "columns_added", "removed",
                              "added", "changed"))


def fmt_key(keys, k):
    return ", ".join(f"{c}={v!r}" for c, v in zip(keys, k))


def report_text(r, keys, limit):
    out = []

    def section(title, items, render):
        if not items:
            return
        out.append(f"{title} ({len(items)}):")
        for it in items[:limit]:
            out.append("  " + render(it))
        if len(items) > limit:
            out.append(f"  ... {len(items) - limit} more (raise --limit)")

    section("Columns only in OLD", r["columns_removed"], str)
    section("Columns only in NEW", r["columns_added"], str)
    section("Rows removed", r["removed"], lambda k: fmt_key(keys, k))
    section("Rows added", r["added"], lambda k: fmt_key(keys, k))
    section("Rows changed", r["changed"], lambda c: fmt_key(keys, c["key"]) + " | " +
            "; ".join(f"{col}: {a!r} -> {b!r}" for col, (a, b) in c["cells"].items()))
    section("Duplicate keys in OLD (later rows ignored)", r["duplicate_keys_old"],
            lambda d: f"line {d[1]}: {fmt_key(keys, d[0])}")
    section("Duplicate keys in NEW (later rows ignored)", r["duplicate_keys_new"],
            lambda d: f"line {d[1]}: {fmt_key(keys, d[0])}")
    out.append(f"Summary: {len(r['added'])} added, {len(r['removed'])} removed, "
               f"{len(r['changed'])} changed, {r['unchanged']} unchanged")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(
        prog="csv-diff",
        description="Compare two CSV files by key column(s). Reports added, removed "
                    "and changed rows and column differences. Read-only; never "
                    "modifies files or uses the network.",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("old", help="original CSV file")
    p.add_argument("new", help="updated CSV file")
    p.add_argument("-k", "--key", required=True,
                   help="comma-separated key column(s) identifying a row")
    p.add_argument("-d", "--delimiter", default=",",
                   help="field delimiter (default ','; use '\\t' for tabs)")
    p.add_argument("-i", "--ignore", default="",
                   help="comma-separated columns to exclude from comparison")
    p.add_argument("--trim", action="store_true",
                   help="strip surrounding whitespace from all cells before comparing")
    p.add_argument("-f", "--format", choices=("text", "json"), default="text",
                   help="output format (default: text)")
    p.add_argument("-n", "--limit", type=int, default=50,
                   help="max items shown per section in text mode (default 50)")
    a = p.parse_args()

    delim = "\t" if a.delimiter == "\\t" else a.delimiter
    if len(delim) != 1:
        die("delimiter must be a single character")
    keys = [k.strip() for k in a.key.split(",") if k.strip()]
    if not keys:
        die("--key needs at least one column name")
    ignore = {c.strip() for c in a.ignore.split(",") if c.strip()}

    old = load(a.old, keys, delim, a.trim)
    new = load(a.new, keys, delim, a.trim)
    result = diff(old, new, keys, ignore)

    if a.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(report_text(result, keys, max(a.limit, 0)))
    sys.exit(1 if has_diff(result) else 0)


if __name__ == "__main__":
    main()
