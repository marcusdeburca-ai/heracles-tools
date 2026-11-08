#!/usr/bin/env python3
"""json-shape: summarize the structure of JSON / JSONL files.

Walks every value, records the JSON types seen at each path (arrays are
written as `[]`), counts occurrences, shows how often each key is present
in its parent object, and flags paths with mixed types. Read-only: it only
opens the files you name and never uses the network.
"""
import argparse
import json
import sys
from collections import Counter

EPILOG = """\
examples:
  json-shape data.json
  json-shape --jsonl events.jsonl --strict
  json-shape a.json b.json --max-depth 3 --format json

exit codes: 0 ok, 1 mixed types found with --strict, 2 a file could not be read/parsed
"""


def type_name(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    return "object"


class Shape:
    def __init__(self, max_depth):
        self.max_depth = max_depth
        self.types = {}          # path -> Counter of type names
        self.objects = Counter()  # path -> number of objects seen at path
        self.parent = {}         # key path -> parent object path

    def walk(self, v, path, depth=0):
        t = type_name(v)
        self.types.setdefault(path, Counter())[t] += 1
        if depth >= self.max_depth:
            return
        if isinstance(v, dict):
            self.objects[path] += 1
            for k, x in v.items():
                child = f"{path}.{k}" if path else k
                self.parent[child] = path
                self.walk(x, child, depth + 1)
        elif isinstance(v, list):
            child = f"{path}[]"
            for x in v:
                self.walk(x, child, depth + 1)

    def rows(self):
        out = []
        for path, counter in self.types.items():
            kinds = set(counter)
            if kinds == {"integer", "number"}:
                kinds_cmp = {"number"}
            else:
                kinds_cmp = kinds - {"null"}
                if "integer" in kinds_cmp and "number" in kinds_cmp:
                    kinds_cmp.discard("integer")
            mixed = len(kinds_cmp) > 1
            present = None
            if path in self.parent:
                total = self.objects[self.parent[path]]
                present = (sum(counter.values()), total)
            out.append({
                "path": path or "$",
                "types": dict(counter),
                "count": sum(counter.values()),
                "present_in": present,
                "mixed": mixed,
            })
        return out


def load(path, jsonl):
    with open(path, "r", encoding="utf-8-sig") as f:
        if not jsonl:
            yield json.load(f)
            return
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"line {n}: {e}") from e


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="json-shape",
        description="Summarize the structure (paths, types, optional keys) of JSON or JSONL files.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", help="input files; all are merged into one summary")
    p.add_argument("--jsonl", action="store_true", help="treat files as JSON Lines (one value per line)")
    p.add_argument("--max-depth", type=int, default=50, help="do not descend deeper than N levels (default 50)")
    p.add_argument("--format", choices=["text", "json"], default="text", help="output format (default text)")
    p.add_argument("--strict", action="store_true", help="exit 1 if any path has mixed types")
    args = p.parse_args(argv)

    shape = Shape(args.max_depth)
    failed = False
    for fn in args.files:
        try:
            for value in load(fn, args.jsonl):
                shape.walk(value, "")
        except (OSError, ValueError) as e:
            print(f"json-shape: {fn}: {e}", file=sys.stderr)
            failed = True

    rows = shape.rows()
    if args.format == "json":
        print(json.dumps(rows, indent=2))
    else:
        width = max([len(r["path"]) for r in rows] + [4])
        print(f"{'PATH':<{width}}  {'TYPES':<28} {'COUNT':>7}  PRESENT  FLAGS")
        for r in rows:
            types = "|".join(f"{k}" for k in sorted(r["types"]))
            pres = ""
            flags = []
            if r["present_in"]:
                n, total = r["present_in"]
                pres = f"{n}/{total}"
                if n < total:
                    flags.append("optional")
            if r["mixed"]:
                flags.append("MIXED")
            print(f"{r['path']:<{width}}  {types:<28} {r['count']:>7}  {pres:<7}  {' '.join(flags)}")
        mixed = sum(1 for r in rows if r["mixed"])
        print(f"\n{len(rows)} paths, {mixed} with mixed types", file=sys.stderr)

    if failed:
        return 2
    if args.strict and any(r["mixed"] for r in rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
