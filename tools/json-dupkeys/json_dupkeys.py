#!/usr/bin/env python3
"""json-dupkeys: report duplicate keys in JSON / JSONL files.

Standard JSON parsers silently keep only the last value for a repeated key,
which hides copy-paste mistakes in configs and data dumps. This tool parses
each file, records every repeated key, and prints the JSON path of the object
that contains it.

Exit codes: 0 = no duplicates, 1 = duplicates found, 2 = unreadable/invalid input.
Read-only: it never modifies or deletes files and never uses the network.
"""
import argparse
import json
import sys


class DupDict(dict):
    """dict that remembers keys which appeared more than once while parsing."""
    dups = None


def hook(pairs):
    d = DupDict()
    seen = {}
    for key, value in pairs:
        seen.setdefault(key, []).append(value)
        d[key] = value  # same "last wins" behaviour as the normal parser
    d.dups = {k: v for k, v in seen.items() if len(v) > 1}
    return d


def join_path(path, key):
    if isinstance(key, int):
        return "%s[%d]" % (path, key)
    if key.isidentifier():
        return "%s.%s" % (path, key)
    return "%s[%s]" % (path, json.dumps(key))


def walk(node, path, found):
    """Collect (path, key, values) for every duplicate in the parsed tree."""
    if isinstance(node, dict):
        if isinstance(node, DupDict) and node.dups:
            for key, values in node.dups.items():
                found.append((path, key, values))
        for key, child in node.items():
            walk(child, join_path(path, key), found)
    elif isinstance(node, list):
        for i, child in enumerate(node):
            walk(child, join_path(path, i), found)


def canon(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def describe(key, values):
    distinct = {canon(v) for v in values}
    if len(distinct) == 1:
        note = "identical values"
    else:
        note = "CONFLICTING values, last wins: %s" % canon(values[-1])
    return "key %s appears %d times (%s)" % (json.dumps(key, ensure_ascii=False), len(values), note)


def check_document(text, label, out, quiet):
    """Return number of duplicate keys found; raises ValueError on bad JSON."""
    doc = json.loads(text, object_pairs_hook=hook)
    found = []
    walk(doc, "$", found)
    if not quiet:
        for path, key, values in found:
            print("%s: %s: %s" % (label, path, describe(key, values)), file=out)
    return len(found)


def check_file(name, jsonl, quiet):
    if name == "-":
        text = sys.stdin.read()
    else:
        with open(name, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    if not jsonl:
        return check_document(text, name, sys.stdout, quiet)
    total = 0
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            total += check_document(line, "%s:%d" % (name, lineno), sys.stdout, quiet)
        except ValueError as exc:
            raise ValueError("line %d: %s" % (lineno, exc))
    return total


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="json-dupkeys",
        description="Detect duplicate keys in JSON objects, which normal parsers silently drop. "
                    "Reports the JSON path of each affected object and whether the repeated "
                    "values differ.",
        epilog="Examples:\n"
               "  json-dupkeys config.json\n"
               "  json-dupkeys --jsonl events.jsonl other.jsonl\n"
               "  cat data.json | json-dupkeys -\n"
               "Exit codes: 0 clean, 1 duplicates found, 2 read/parse error.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", metavar="FILE", help="JSON files to check ('-' reads stdin)")
    p.add_argument("--jsonl", action="store_true",
                   help="treat each non-blank line as a separate JSON document")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="print only the summary and errors, not each duplicate")
    args = p.parse_args(argv)

    dup_total = 0
    files_with_dups = 0
    errors = 0
    for name in args.files:
        try:
            n = check_file(name, args.jsonl, args.quiet)
        except (OSError, UnicodeDecodeError, ValueError, RecursionError) as exc:
            print("%s: error: %s" % (name, exc), file=sys.stderr)
            errors += 1
            continue
        if n:
            dup_total += n
            files_with_dups += 1
        elif not args.quiet:
            print("%s: ok" % name)

    print("checked %d file(s): %d duplicate key(s) in %d file(s), %d error(s)"
          % (len(args.files), dup_total, files_with_dups, errors), file=sys.stderr)
    if errors:
        return 2
    return 1 if dup_total else 0


if __name__ == "__main__":
    sys.exit(main())
