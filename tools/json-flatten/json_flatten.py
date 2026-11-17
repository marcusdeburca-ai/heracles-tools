#!/usr/bin/env python3
"""json-flatten: turn nested JSON / JSONL into one `path<TAB>value` line per leaf.

Read-only, standard library only, no network access.
"""
import argparse
import json
import re
import sys

EXAMPLES = """\
examples:
  json-flatten config.json
  json-flatten --grep user data.json | head
  json-flatten --jsonl events.jsonl --paths
  json-flatten --max-depth 2 big.json
  json-flatten a.json b.json            # lines are prefixed with the file name

Path syntax is jq-like: $.users[0].name ; keys containing '.', '[', ']'
or that are empty are written as $["odd.key"].
"""


def type_name(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, dict):
        return "object"
    return "array"


def key_path(parent, key):
    if key == "" or any(c in key for c in ".[]\""):
        return "%s[%s]" % (parent, json.dumps(key))
    return "%s.%s" % (parent, key)


def flatten(obj, path="$", max_depth=None, depth=0):
    """Yield (path, value) for every leaf. Empty containers count as leaves."""
    if isinstance(obj, dict) and obj:
        if max_depth is not None and depth >= max_depth:
            yield path, obj
            return
        for k, v in obj.items():
            yield from flatten(v, key_path(path, k), max_depth, depth + 1)
    elif isinstance(obj, list) and obj:
        if max_depth is not None and depth >= max_depth:
            yield path, obj
            return
        for i, v in enumerate(obj):
            yield from flatten(v, "%s[%d]" % (path, i), max_depth, depth + 1)
    else:
        yield path, obj


def documents(fh, jsonl, name, errors):
    """Yield (line_number_or_None, parsed_value). Record problems in errors."""
    if not jsonl:
        try:
            yield None, json.load(fh)
        except json.JSONDecodeError as e:
            errors.append("%s: invalid JSON at line %d col %d: %s" % (name, e.lineno, e.colno, e.msg))
        return
    for n, line in enumerate(fh, 1):
        if not line.strip():
            continue
        try:
            yield n, json.loads(line)
        except json.JSONDecodeError as e:
            errors.append("%s:%d: invalid JSON: %s" % (name, n, e.msg))


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="json-flatten",
        description="Flatten JSON or JSONL files into `path<TAB>value` lines so they "
                    "can be grepped, sorted and diffed. Never modifies the inputs.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", help="JSON files to read ('-' for stdin)")
    p.add_argument("--jsonl", action="store_true", help="treat each non-blank line as a separate JSON document")
    p.add_argument("--max-depth", type=int, metavar="N",
                   help="stop descending after N levels; deeper values print as compact JSON")
    p.add_argument("--grep", metavar="TEXT", help="only show paths containing TEXT (case-insensitive)")
    p.add_argument("--paths", action="store_true",
                   help="summarize distinct paths (array indexes become []) with value types and counts")
    p.add_argument("--no-prefix", action="store_true", help="never prefix lines with file name / line number")
    args = p.parse_args(argv)

    errors = []
    summary = {}  # normalized path -> {type: count}
    multi = len(args.files) > 1
    needle = args.grep.lower() if args.grep else None

    for name in args.files:
        try:
            fh = sys.stdin if name == "-" else open(name, encoding="utf-8-sig")
        except OSError as e:
            errors.append("%s: cannot open: %s" % (name, e.strerror or e))
            continue
        try:
            for lineno, doc in documents(fh, args.jsonl, name, errors):
                for path, value in flatten(doc, "$", args.max_depth):
                    if needle and needle not in path.lower():
                        continue
                    if args.paths:
                        norm = re.sub(r"\[\d+\]", "[]", path)
                        t = type_name(value)
                        counts = summary.setdefault(norm, {})
                        counts[t] = counts.get(t, 0) + 1
                        continue
                    prefix = []
                    if multi and not args.no_prefix:
                        prefix.append(name)
                    if lineno is not None and not args.no_prefix:
                        prefix.append(str(lineno))
                    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    head = (":".join(prefix) + "\t") if prefix else ""
                    print("%s%s\t%s" % (head, path, text))
        except UnicodeDecodeError as e:
            errors.append("%s: not valid UTF-8 (%s)" % (name, e.reason))
        finally:
            if fh is not sys.stdin:
                fh.close()

    if args.paths:
        for path in sorted(summary):
            kinds = ", ".join("%s x%d" % (t, c) for t, c in sorted(summary[path].items()))
            print("%s\t%s" % (path, kinds))

    for e in errors:
        print("json-flatten: " + e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
