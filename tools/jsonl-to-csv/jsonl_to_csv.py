#!/usr/bin/env python3
"""jsonl-to-csv: convert JSON Lines files to CSV (standard library only)."""
import argparse
import csv
import json
import sys

EPILOG = """examples:
  jsonl-to-csv events.jsonl > events.csv
  jsonl-to-csv a.jsonl b.jsonl -o merged.csv
  jsonl-to-csv logs.jsonl --flatten --columns id,user.name,status

exit codes: 0 ok, 1 some lines were skipped, 2 usage/file error.
"""


def flatten(obj, prefix="", out=None):
    """Flatten nested non-empty dicts into dotted keys."""
    out = {} if out is None else out
    for k, v in obj.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and v:
            flatten(v, key + ".", out)
        else:
            out[key] = v
    return out


def cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return v


def load(paths, flat, strict):
    """Return (records, bad_count). Bad lines are reported on stderr."""
    records, bad = [], 0
    for path in paths:
        try:
            f = open(path, encoding="utf-8-sig")
        except OSError as e:
            sys.exit(f"error: cannot open {path}: {e.strerror}")
        with f:
            try:
                for n, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    problem = None
                    try:
                        obj = json.loads(line)
                        if not isinstance(obj, dict):
                            problem = f"expected an object, got {type(obj).__name__}"
                    except json.JSONDecodeError as e:
                        problem = f"invalid JSON ({e.msg} at column {e.colno})"
                    if problem:
                        bad += 1
                        print(f"{path}:{n}: {problem}", file=sys.stderr)
                        if strict:
                            sys.exit(1)
                        continue
                    records.append(flatten(obj) if flat else obj)
            except UnicodeDecodeError as e:
                sys.exit(f"error: {path} is not valid UTF-8: {e.reason}")
    return records, bad


def main():
    ap = argparse.ArgumentParser(
        prog="jsonl-to-csv",
        description="Convert JSON Lines (one JSON object per line) to CSV. "
        "Columns are the union of all keys in first-seen order. Nested "
        "values are written as compact JSON unless --flatten is used. "
        "Malformed lines are reported to stderr and skipped.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("files", nargs="+", metavar="FILE", help="input .jsonl file(s), read as UTF-8")
    ap.add_argument("-o", "--output", help="write CSV here instead of stdout (refuses to overwrite an existing file)")
    ap.add_argument("-c", "--columns", help="comma-separated columns to output, in order (missing values are blank)")
    ap.add_argument("--flatten", action="store_true", help="expand nested objects into dotted columns like user.name")
    ap.add_argument("--strict", action="store_true", help="stop at the first malformed line")
    ap.add_argument("--no-header", action="store_true", help="omit the header row")
    args = ap.parse_args()

    records, bad = load(args.files, args.flatten, args.strict)

    if args.columns:
        columns = [c.strip() for c in args.columns.split(",") if c.strip()]
    else:
        columns, seen = [], set()
        for r in records:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    columns.append(k)

    if args.output:
        try:
            out = open(args.output, "x", encoding="utf-8", newline="")
        except FileExistsError:
            sys.exit(f"error: {args.output} already exists; choose another name")
        except OSError as e:
            sys.exit(f"error: cannot write {args.output}: {e.strerror}")
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", newline="")
        out = sys.stdout

    try:
        w = csv.writer(out, lineterminator="\n")
        if not args.no_header:
            w.writerow(columns)
        for r in records:
            w.writerow([cell(r.get(c)) for c in columns])
    finally:
        if out is not sys.stdout:
            out.close()

    print(f"{len(records)} rows, {len(columns)} columns, {bad} lines skipped", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
