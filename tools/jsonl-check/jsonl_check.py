#!/usr/bin/env python3
"""jsonl-check: validate JSON Lines (.jsonl / .ndjson) files.

Reads files given as arguments (use '-' for stdin). Never writes, deletes,
or uses the network.
"""
import argparse
import collections
import json
import sys

EPILOG = """\
exit status:
  0  all files clean
  1  problems found (bad lines, missing keys, or mixed types with --strict-types)
  2  a file could not be read

examples:
  jsonl-check events.jsonl
  jsonl-check --require id,timestamp logs/*.jsonl
  jsonl-check --object-only --strict-types --show-keys data.jsonl
"""


class DuplicateKey(ValueError):
    pass


def _pairs(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise DuplicateKey("duplicate key %r" % key)
        seen.add(key)
    return dict(pairs)


def _bad_constant(name):
    raise ValueError("non-standard constant %s" % name)


def type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def check_stream(handle, args, required):
    stats = {
        "lines": 0, "blank": 0, "valid": 0, "invalid": 0,
        "missing": 0, "problems": [],
    }
    key_types = collections.defaultdict(collections.Counter)

    def report(lineno, msg):
        if len(stats["problems"]) < args.max_errors:
            stats["problems"].append("  line %d: %s" % (lineno, msg))

    for lineno, raw in enumerate(handle, 1):
        stats["lines"] += 1
        text = raw.strip()
        if not text:
            stats["blank"] += 1
            if args.no_blank:
                stats["invalid"] += 1
                report(lineno, "blank line")
            continue
        try:
            value = json.loads(text, object_pairs_hook=_pairs,
                               parse_constant=_bad_constant)
        except json.JSONDecodeError as exc:
            stats["invalid"] += 1
            report(lineno, "invalid JSON (%s)" % exc.msg)
            continue
        except (ValueError, RecursionError) as exc:
            stats["invalid"] += 1
            report(lineno, "invalid JSON (%s)" % exc)
            continue
        if args.object_only and not isinstance(value, dict):
            stats["invalid"] += 1
            report(lineno, "expected object, got %s" % type_name(value))
            continue
        stats["valid"] += 1
        if isinstance(value, dict):
            missing = [k for k in required if k not in value]
            if missing:
                stats["missing"] += 1
                report(lineno, "missing required key(s): " + ", ".join(missing))
            for key, val in value.items():
                key_types[key][type_name(val)] += 1
        elif required:
            stats["missing"] += 1
            report(lineno, "not an object; cannot have required keys")
    return stats, key_types


def mixed_keys(key_types):
    """Keys with more than one non-null type."""
    out = {}
    for key, counter in key_types.items():
        real = [t for t in counter if t != "null"]
        if len(real) > 1:
            out[key] = counter
    return out


def fmt_counter(counter):
    return ", ".join("%s=%d" % (t, n) for t, n in counter.most_common())


def process(path, args, required):
    if path == "-":
        return check_stream(sys.stdin, args, required)
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return check_stream(handle, args, required)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jsonl-check",
        description="Validate JSON Lines files: syntax, duplicate keys, "
                    "required keys, and per-key type consistency.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", help="input files ('-' for stdin)")
    parser.add_argument("--require", metavar="KEYS", default="",
                        help="comma-separated keys every object must contain")
    parser.add_argument("--object-only", action="store_true",
                        help="treat non-object lines (e.g. 1, [..]) as invalid")
    parser.add_argument("--no-blank", action="store_true",
                        help="treat blank lines as invalid (default: skipped)")
    parser.add_argument("--strict-types", action="store_true",
                        help="exit 1 if a key holds mixed types (null ignored)")
    parser.add_argument("--show-keys", action="store_true",
                        help="print every key with its type counts")
    parser.add_argument("--max-errors", type=int, default=20, metavar="N",
                        help="max problem lines listed per file (default 20)")
    args = parser.parse_args(argv)

    required = [k.strip() for k in args.require.split(",") if k.strip()]
    status = 0
    for path in args.files:
        try:
            stats, key_types = process(path, args, required)
        except OSError as exc:
            print("%s: cannot read (%s)" % (path, exc.strerror or exc),
                  file=sys.stderr)
            status = max(status, 2)
            continue
        print("%s: %d lines, %d valid, %d invalid, %d blank, "
              "%d missing required" % (path, stats["lines"], stats["valid"],
                                       stats["invalid"], stats["blank"],
                                       stats["missing"]))
        for line in stats["problems"]:
            print(line)
        total = stats["invalid"] + stats["missing"]
        if total > len(stats["problems"]):
            print("  ... %d more not shown" % (total - len(stats["problems"])))
        if stats["invalid"] or stats["missing"]:
            status = max(status, 1)
        mixed = mixed_keys(key_types)
        for key in sorted(mixed):
            print("  mixed types for %r: %s" % (key, fmt_counter(mixed[key])))
        if mixed and args.strict_types:
            status = max(status, 1)
        if args.show_keys:
            for key in sorted(key_types):
                print("  key %r: %s" % (key, fmt_counter(key_types[key])))
    return status


if __name__ == "__main__":
    sys.exit(main())
