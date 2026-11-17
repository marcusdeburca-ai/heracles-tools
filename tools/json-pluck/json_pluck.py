#!/usr/bin/env python3
"""json-pluck: extract fields from JSON / JSONL files into CSV, TSV or JSONL."""
import argparse
import csv
import json
import sys

MISSING = object()

EPILOG = """\
examples:
  json-pluck -f id -f user.name data.json
  json-pluck -f id -f city=address.city --root results users.json
  json-pluck -f items.0.sku -f tags --source logs.jsonl > out.csv
  json-pluck -f id --format tsv --strict a.json b.jsonl

Paths are dotted: keys by name, list items by integer index (items.0, items.-1).
Use alias=path to rename a column. Input may be a JSON document or JSONL.
Exit codes: 0 ok, 1 unreadable/invalid input, 2 --strict and a path was missing.
"""


def get_path(obj, parts):
    for p in parts:
        if isinstance(obj, dict) and p in obj:
            obj = obj[p]
        elif isinstance(obj, list) and p.lstrip("-").isdigit() and -len(obj) <= int(p) < len(obj):
            obj = obj[int(p)]
        else:
            return MISSING
    return obj


def parse_field(spec):
    if "=" in spec:
        name, path = spec.split("=", 1)
    else:
        name, path = spec, spec
    if not name or not path:
        raise argparse.ArgumentTypeError("bad field spec %r" % spec)
    return name, path.split(".")


def records_from(path, root, err):
    """Yield (label, record) pairs from one file."""
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        err("%s: cannot read: %s" % (path, exc))
        return
    try:
        data = json.loads(text)
        docs = [("", data)]
    except json.JSONDecodeError:
        docs = []
        for n, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                docs.append((":%d" % n, json.loads(line)))
            except json.JSONDecodeError as exc:
                err("%s:%d: invalid JSON: %s" % (path, n, exc.msg))
    single = len(docs) == 1 and docs[0][0] == ""
    for label, doc in docs:
        if root:
            doc = get_path(doc, root.split("."))
            if doc is MISSING:
                err("%s%s: root path %r not found" % (path, label, root))
                continue
        if single and isinstance(doc, list):
            for i, item in enumerate(doc):
                yield "%s[%d]" % (path, i), item
        else:
            yield path + label, doc


def fmt(value):
    if value is MISSING or value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return str(value)


def main():
    ap = argparse.ArgumentParser(
        description="Extract fields from JSON/JSONL files by dotted path. "
                    "Read-only; never touches the network; writes to stdout.",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="JSON or JSONL input files")
    ap.add_argument("-f", "--field", action="append", required=True, type=parse_field,
                    metavar="[NAME=]PATH", help="field to extract (repeatable)")
    ap.add_argument("--root", help="dotted path to the array/object holding the records")
    ap.add_argument("--format", choices=["csv", "tsv", "jsonl"], default="csv",
                    help="output format (default: csv)")
    ap.add_argument("--no-header", action="store_true", help="omit the header row")
    ap.add_argument("--source", action="store_true",
                    help="add a _source column with file name and position")
    ap.add_argument("--strict", action="store_true",
                    help="report missing paths and exit 2 if any are found")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", newline="")
    problems = []
    err = lambda m: (problems.append(m), print(m, file=sys.stderr))
    missing = 0
    names = [n for n, _ in args.field]
    if args.source:
        names = ["_source"] + names

    writer = None
    if args.format != "jsonl":
        writer = csv.writer(sys.stdout, delimiter="\t" if args.format == "tsv" else ",",
                            lineterminator="\n")
        if not args.no_header:
            writer.writerow(names)

    for path in args.files:
        for label, rec in records_from(path, args.root, err):
            vals = [get_path(rec, parts) for _, parts in args.field]
            for (name, _), v in zip(args.field, vals):
                if v is MISSING:
                    missing += 1
                    if args.strict:
                        print("%s: missing %r" % (label, name), file=sys.stderr)
            if args.format == "jsonl":
                row = {n: (None if v is MISSING else v) for n, v in zip(names[args.source:], vals)}
                if args.source:
                    row = dict(_source=label, **row)
                print(json.dumps(row, ensure_ascii=False))
            else:
                out = [fmt(v) for v in vals]
                writer.writerow(([label] if args.source else []) + out)

    if problems:
        return 1
    if args.strict and missing:
        print("%d missing value(s)" % missing, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
