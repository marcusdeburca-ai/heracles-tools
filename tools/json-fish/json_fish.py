#!/usr/bin/env python3
"""json-fish: pull valid JSON values out of messy text files."""
import argparse
import json
import sys

DESCRIPTION = """\
Scan text files (LLM replies, logs, markdown with ```json fences, emails...)
and extract every valid JSON object/array embedded in them. Invalid
fragments are skipped. Input files are only read, never modified.
"""

EPILOG = """\
examples:
  json-fish reply.txt                    pretty-print every JSON value found
  json-fish --first --only objects a.md  first JSON object in a.md
  json-fish --jsonl logs/*.txt           one compact value per line
  json-fish --get user.tags.0 reply.txt  pick a nested field (dotted path)
  json-fish --locations reply.txt        show file:line of each match

exit codes: 0 = something found, 1 = nothing found, 2 = a file could not be read
"""


def scan(text):
    """Yield (value, start_index, end_index) for each JSON object/array in text."""
    decoder = json.JSONDecoder()
    n = len(text)
    i = 0
    while i < n:
        if text[i] not in "{[":
            nxt = [p for p in (text.find("{", i), text.find("[", i)) if p != -1]
            if not nxt:
                return
            i = min(nxt)
        try:
            value, end = decoder.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        yield value, i, end
        i = end


def dig(value, path):
    """Follow a dotted path through dicts and lists. Raises KeyError if absent."""
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.lstrip("-").isdigit():
            try:
                value = value[int(part)]
            except IndexError:
                raise KeyError(part)
        else:
            raise KeyError(part)
    return value


def keep(value, only, min_items):
    if only == "objects" and not isinstance(value, dict):
        return False
    if only == "arrays" and not isinstance(value, list):
        return False
    return len(value) >= min_items


def read_text(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


def build_parser():
    p = argparse.ArgumentParser(
        prog="json-fish",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", help="input files ('-' reads stdin)")
    p.add_argument("--only", choices=["any", "objects", "arrays"], default="any",
                   help="keep only objects or only arrays (default: any)")
    p.add_argument("--min-items", type=int, default=1, metavar="N",
                   help="skip values with fewer than N keys/items (default: 1, "
                        "which drops empty {} and [])")
    p.add_argument("--get", metavar="PATH",
                   help="dotted path to select from each value, e.g. a.b.0; "
                        "values lacking the path are skipped")
    p.add_argument("--first", action="store_true",
                   help="stop after the first match in each file")
    p.add_argument("--jsonl", action="store_true",
                   help="print each value compact on one line")
    p.add_argument("--indent", type=int, default=2,
                   help="indent for pretty output (default: 2)")
    p.add_argument("--sort-keys", action="store_true", help="sort object keys")
    p.add_argument("--locations", action="store_true",
                   help="print 'file:line' for each match to stderr")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    found = 0
    errors = 0
    for path in args.files:
        try:
            text = read_text(path)
        except (OSError, UnicodeError) as exc:
            print(f"json-fish: cannot read {path}: {exc}", file=sys.stderr)
            errors += 1
            continue
        for value, start, _end in scan(text):
            if not keep(value, args.only, args.min_items):
                continue
            if args.get:
                try:
                    value = dig(value, args.get)
                except KeyError:
                    continue
            found += 1
            if args.locations:
                line = text.count("\n", 0, start) + 1
                print(f"{path}:{line}", file=sys.stderr)
            if args.jsonl:
                out = json.dumps(value, ensure_ascii=False,
                                 separators=(",", ":"), sort_keys=args.sort_keys)
            else:
                out = json.dumps(value, ensure_ascii=False,
                                 indent=args.indent, sort_keys=args.sort_keys)
            print(out)
            if args.first:
                break
    if errors:
        return 2
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
