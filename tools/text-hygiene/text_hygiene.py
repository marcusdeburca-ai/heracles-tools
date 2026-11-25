#!/usr/bin/env python3
"""text-hygiene: report common whitespace/encoding problems in text files.

Read-only: files are never modified or deleted, and no network is used.
"""
import argparse
import json
import re
import sys

EPILOG = """\
checks:
  bom               file starts with a UTF-8 byte order mark
  invalid-utf8      file is not valid UTF-8 (first bad byte offset is shown)
  mixed-endings     more than one of CRLF / LF / CR is used
  no-final-newline  last line has no line terminator
  trailing-space    line ends with spaces or tabs
  tab-indent        line starts with a tab
  control-char      NUL or other control characters (not tab/CR/LF)
  invisible-char    zero-width space/joiner, NBSP, or BOM inside the text

exit codes: 0 clean (or --report-only), 1 problems found, 2 unreadable file
examples:
  text-hygiene notes.txt README.md
  text-hygiene --only trailing-space,tab-indent src.py
  text-hygiene --json --max-examples 3 data.csv
"""

CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
INVISIBLE = re.compile("[\u00a0\u200b\u200c\u200d\u2060\ufeff]")
SPLIT = re.compile(r"\r\n|\n|\r")
CHECKS = ["bom", "invalid-utf8", "mixed-endings", "no-final-newline",
          "trailing-space", "tab-indent", "control-char", "invisible-char"]


def analyze(path):
    with open(path, "rb") as fh:
        data = fh.read()
    found = {}  # check -> list of line numbers (0 = whole file)

    def add(name, line=0):
        found.setdefault(name, []).append(line)

    if data.startswith(b"\xef\xbb\xbf"):
        add("bom")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        add("invalid-utf8", 0)
        found["invalid-utf8"] = [0]
        text = data.decode("utf-8", errors="replace")
        found_offset = exc.start
    else:
        found_offset = None

    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    cr = data.count(b"\r") - crlf
    endings = {"CRLF": crlf, "LF": lf, "CR": cr}
    if sum(1 for v in endings.values() if v) > 1:
        add("mixed-endings")

    if text.startswith("\ufeff"):
        text = text[1:]  # BOM already reported; don't flag it as invisible
    lines = SPLIT.split(text)
    if lines and lines[-1] == "":
        lines.pop()
    elif text:
        add("no-final-newline")

    for n, line in enumerate(lines, 1):
        if line != line.rstrip(" \t"):
            add("trailing-space", n)
        if line.startswith("\t"):
            add("tab-indent", n)
        if CONTROL.search(line):
            add("control-char", n)
        if INVISIBLE.search(line):
            add("invisible-char", n)

    return {"file": path, "lines": len(lines), "endings": endings,
            "bad_byte_offset": found_offset, "issues": found}


def render(res, max_examples, only):
    out = []
    issues = {k: v for k, v in res["issues"].items() if not only or k in only}
    ends = ", ".join(f"{k}={v}" for k, v in res["endings"].items() if v) or "none"
    head = f"{res['file']}: {res['lines']} lines, endings: {ends}"
    if not issues:
        return [head + " - OK"]
    out.append(head)
    for name in CHECKS:
        if name not in issues:
            continue
        nums = issues[name]
        detail = ""
        if name == "invalid-utf8":
            detail = f" (first bad byte at offset {res['bad_byte_offset']})"
        elif nums and nums[0]:
            shown = ", ".join(map(str, nums[:max_examples]))
            more = len(nums) - max_examples
            detail = f" on {len(nums)} line(s): {shown}" + (f" (+{more} more)" if more > 0 else "")
        out.append(f"  {name}{detail}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="text-hygiene",
        description="Report whitespace and encoding problems in text files. Never modifies files.",
        epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="text files to inspect")
    ap.add_argument("--max-examples", type=int, default=5, metavar="N",
                    help="max line numbers listed per check (default 5)")
    ap.add_argument("--only", metavar="LIST",
                    help="comma-separated checks to report (default: all)")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--report-only", action="store_true",
                    help="always exit 0 when files are readable")
    args = ap.parse_args(argv)

    only = None
    if args.only:
        only = {s.strip() for s in args.only.split(",") if s.strip()}
        bad = only - set(CHECKS)
        if bad:
            ap.error("unknown check(s): " + ", ".join(sorted(bad)))

    status = 0
    results = []
    for path in args.files:
        try:
            res = analyze(path)
        except OSError as exc:
            print(f"text-hygiene: cannot read {path}: {exc.strerror or exc}", file=sys.stderr)
            status = 2
            continue
        results.append(res)
        has = any(k in res["issues"] for k in (only or CHECKS))
        if has and status == 0 and not args.report_only:
            status = 1
        if not args.json:
            print("\n".join(render(res, args.max_examples, only)))

    if args.json:
        for res in results:
            res["issues"] = {k: v for k, v in res["issues"].items()
                             if not only or k in only}
        print(json.dumps(results, indent=2))
    return status


if __name__ == "__main__":
    sys.exit(main())
