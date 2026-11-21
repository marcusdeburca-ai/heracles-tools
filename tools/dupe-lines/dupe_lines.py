#!/usr/bin/env python3
"""dupe-lines: report duplicate lines in one or more text files.

Read-only: files are opened for reading only, nothing is modified or deleted,
and no network access is used.
"""
import argparse
import sys
from collections import OrderedDict

EPILOG = """\
examples:
  dupe-lines hosts.txt
  dupe-lines -i -w emails.txt            ignore case and surrounding whitespace
  dupe-lines --across a.txt b.txt        find lines repeated between files
  dupe-lines --min-count 3 log.txt       only lines appearing 3+ times
  dupe-lines --include-blank notes.txt   also count empty lines

exit status: 0 = no duplicates, 1 = duplicates found, 2 = error reading a file
"""


def build_parser():
    p = argparse.ArgumentParser(
        prog="dupe-lines",
        description="Find duplicate lines in text files and report counts "
                    "and line numbers. Files are never modified.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", metavar="FILE", help="text file(s) to scan")
    p.add_argument("-i", "--ignore-case", action="store_true",
                   help="compare lines case-insensitively")
    p.add_argument("-w", "--strip", action="store_true",
                   help="ignore leading/trailing whitespace when comparing")
    p.add_argument("--include-blank", action="store_true",
                   help="count blank lines too (skipped by default)")
    p.add_argument("--across", action="store_true",
                   help="treat all files as one pool instead of scanning each separately")
    p.add_argument("-n", "--min-count", type=int, default=2, metavar="N",
                   help="report lines occurring at least N times (default: 2)")
    p.add_argument("--max-width", type=int, default=60, metavar="W",
                   help="truncate displayed line text to W characters (default: 60)")
    p.add_argument("--max-locations", type=int, default=10, metavar="K",
                   help="list at most K locations per duplicate (default: 10)")
    p.add_argument("--encoding", default="utf-8",
                   help="input encoding (default: utf-8; undecodable bytes are replaced)")
    return p


def make_key(line, args):
    text = line.rstrip("\r\n")
    if args.strip:
        text = text.strip()
    if args.ignore_case:
        text = text.casefold()
    return text


def scan(path, pool, args):
    """Add (path, lineno, original_text) entries into pool keyed by comparison key."""
    with open(path, "r", encoding=args.encoding, errors="replace", newline=None) as fh:
        for lineno, line in enumerate(fh, 1):
            key = make_key(line, args)
            if not key.strip() and not args.include_blank:
                continue
            pool.setdefault(key, []).append((path, lineno, line.rstrip("\r\n")))


def shorten(text, width):
    text = text.strip() if text.strip() else repr(text)
    return text if len(text) <= width else text[: max(1, width - 3)] + "..."


def report(pool, args, show_path, heading=None):
    groups = [(k, v) for k, v in pool.items() if len(v) >= args.min_count]
    groups.sort(key=lambda kv: (-len(kv[1]), kv[1][0][0], kv[1][0][1]))
    if heading:
        print(heading)
    if not groups:
        print("  no duplicates found" if heading else "no duplicates found")
        return 0, 0
    extra = 0
    for key, entries in groups:
        locs = []
        for path, lineno, _ in entries[: args.max_locations]:
            locs.append(f"{path}:{lineno}" if show_path else str(lineno))
        more = len(entries) - len(locs)
        loc_text = ", ".join(locs) + (f" (+{more} more)" if more > 0 else "")
        print(f"  {len(entries)}x  {shorten(entries[0][2], args.max_width)!r}")
        print(f"       at {'lines ' if not show_path else ''}{loc_text}")
        extra += len(entries) - 1
    return len(groups), extra


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.min_count < 2:
        print("dupe-lines: --min-count must be at least 2", file=sys.stderr)
        return 2

    status = 0
    total_groups = total_extra = 0

    if args.across:
        pool = OrderedDict()
        for path in args.files:
            try:
                scan(path, pool, args)
            except OSError as exc:
                print(f"dupe-lines: cannot read {path}: {exc.strerror or exc}", file=sys.stderr)
                status = 2
        g, e = report(pool, args, show_path=True)
        total_groups += g
        total_extra += e
    else:
        for path in args.files:
            pool = OrderedDict()
            try:
                scan(path, pool, args)
            except OSError as exc:
                print(f"dupe-lines: cannot read {path}: {exc.strerror or exc}", file=sys.stderr)
                status = 2
                continue
            g, e = report(pool, args, show_path=False, heading=f"{path}:")
            total_groups += g
            total_extra += e

    print(f"\nsummary: {total_groups} duplicated line(s), {total_extra} redundant occurrence(s)")
    if status == 0 and total_groups:
        status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
