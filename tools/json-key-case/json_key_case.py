#!/usr/bin/env python3
"""json-key-case: convert JSON object keys between naming styles.

Reads files, writes converted JSON to stdout. Never modifies input files
and never uses the network.
"""
import argparse
import json
import re
import sys

STYLES = ("snake", "camel", "pascal", "kebab")


def split_words(key):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    return [w for w in re.split(r"[^0-9A-Za-z]+", s) if w]


def convert(key, style):
    words = [w.lower() for w in split_words(key)]
    if not words:
        return key  # nothing to convert (e.g. "" or "---")
    if style == "snake":
        return "_".join(words)
    if style == "kebab":
        return "-".join(words)
    if style == "pascal":
        return "".join(w.capitalize() for w in words)
    return words[0] + "".join(w.capitalize() for w in words[1:])


def transform(node, style, path, collisions):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            nk = convert(k, style)
            if nk in out:
                collisions.append("%s: %r -> %r already used" % (path, k, nk))
                continue  # keep the first value, drop the later one
            out[nk] = transform(v, style, path + "." + k, collisions)
        return out
    if isinstance(node, list):
        return [transform(v, style, "%s[%d]" % (path, i), collisions)
                for i, v in enumerate(node)]
    return node


def emit(data, indent):
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def process(path, args):
    """Return (had_parse_error, had_collisions)."""
    collisions = []
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as e:
        print("%s: cannot read: %s" % (path, e), file=sys.stderr)
        return True, False
    as_lines = args.lines or path.lower().endswith(".jsonl")
    try:
        if as_lines:
            for n, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError("line %d: %s" % (n, e))
                emit(transform(obj, args.to, "$[line %d]" % n, collisions), None)
        else:
            obj = json.loads(text)
            emit(transform(obj, args.to, "$", collisions), args.indent)
    except (ValueError, RecursionError) as e:
        print("%s: invalid JSON: %s" % (path, e), file=sys.stderr)
        return True, bool(collisions)
    for c in collisions:
        print("%s: key collision at %s" % (path, c), file=sys.stderr)
    return False, bool(collisions)


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="json-key-case",
        description="Convert all object keys in JSON/JSONL files to a naming "
                    "style and print the result to stdout. Input files are "
                    "only read, never modified.",
        epilog="Exit codes: 0 ok, 1 unreadable/invalid input, 2 key collisions "
               "(colliding later keys are dropped and reported on stderr).\n"
               "Example: json-key-case --to snake api.json > api_snake.json",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="JSON or JSONL files to read")
    p.add_argument("-t", "--to", choices=STYLES, default="snake",
                   help="target style (default: snake)")
    p.add_argument("-i", "--indent", type=int, default=2,
                   help="indent width for JSON output; 0 = compact (default: 2)")
    p.add_argument("-l", "--lines", action="store_true",
                   help="treat every file as JSON Lines (automatic for .jsonl)")
    args = p.parse_args(argv)
    if args.indent <= 0:
        args.indent = None

    bad = coll = False
    for f in args.files:
        b, c = process(f, args)
        bad, coll = bad or b, coll or c
    return 1 if bad else (2 if coll else 0)


if __name__ == "__main__":
    sys.exit(main())
