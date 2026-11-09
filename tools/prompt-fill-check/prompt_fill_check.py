#!/usr/bin/env python3
"""prompt-fill-check: validate and render {{placeholder}} prompt templates against test cases."""
import argparse
import csv
import json
import re
import sys

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][\w.-]*)\s*\}\}")

EPILOG = """\
examples:
  prompt-fill-check prompt.txt cases.csv
  prompt-fill-check prompt.txt cases.jsonl --max-chars 4000
  prompt-fill-check prompt.txt cases.json --render > rendered.txt
  prompt-fill-check prompt.txt cases.csv --render --jsonl > rendered.jsonl

Case files: .csv (header row = variable names), .json (list of objects),
.jsonl (one object per line). Placeholders look like {{name}}.
Exit status: 0 = no errors, 1 = errors found, 2 = bad input/usage.
Nothing is modified; rendered output goes to stdout, diagnostics to stderr.
"""


def load_cases(path):
    if path.lower().endswith(".jsonl"):
        cases = []
        with open(path, encoding="utf-8-sig") as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path}:{n}: invalid JSON ({e.msg})")
                if not isinstance(obj, dict):
                    raise ValueError(f"{path}:{n}: expected a JSON object")
                cases.append(obj)
        return cases
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8-sig") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}: invalid JSON ({e.msg} at line {e.lineno})")
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise ValueError(f"{path}: expected an object or a list of objects")
        return data
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path}: no header row found")
        return [{k: (v if v is not None else "") for k, v in row.items() if k is not None}
                for row in reader]


def as_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def render(template, case):
    def sub(m):
        name = m.group(1)
        return as_text(case[name]) if name in case else m.group(0)
    return PLACEHOLDER.sub(sub, template)


def main():
    p = argparse.ArgumentParser(
        prog="prompt-fill-check",
        description="Validate a prompt template's {{placeholders}} against test cases "
                    "and optionally render the filled-in prompts.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("template", help="prompt template text file")
    p.add_argument("cases", help="test cases: .csv, .json or .jsonl")
    p.add_argument("--render", action="store_true", help="print rendered prompts to stdout")
    p.add_argument("--jsonl", action="store_true",
                   help="with --render, emit one JSON object per case instead of plain text")
    p.add_argument("--max-chars", type=int, default=0, metavar="N",
                   help="flag rendered prompts longer than N characters")
    p.add_argument("--strict", action="store_true",
                   help="treat empty values and unused columns as errors, not warnings")
    args = p.parse_args()

    if args.jsonl and not args.render:
        p.error("--jsonl requires --render")
    try:
        with open(args.template, encoding="utf-8-sig") as f:
            template = f.read()
        cases = load_cases(args.cases)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    wanted = list(dict.fromkeys(PLACEHOLDER.findall(template)))
    if not wanted:
        print("warning: template contains no {{placeholders}}", file=sys.stderr)
    if not cases:
        print("error: no test cases found", file=sys.stderr)
        return 2

    errors, warnings = [], []
    seen_keys = set()
    for i, case in enumerate(cases, 1):
        seen_keys.update(case)
        for name in wanted:
            if name not in case:
                errors.append(f"case {i}: missing variable '{name}'")
            elif not as_text(case[name]).strip():
                (errors if args.strict else warnings).append(
                    f"case {i}: variable '{name}' is empty")
        out = render(template, case)
        if args.max_chars and len(out) > args.max_chars:
            errors.append(f"case {i}: rendered prompt is {len(out)} chars "
                          f"(limit {args.max_chars})")
        if args.render:
            if args.jsonl:
                print(json.dumps({"case": i, "prompt": out}, ensure_ascii=False))
            else:
                print(f"=== case {i} ===")
                print(out)
                print()

    unused = sorted(seen_keys - set(wanted))
    if unused:
        msg = "columns never used by the template: " + ", ".join(unused)
        (errors if args.strict else warnings).append(msg)

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    print(f"{len(cases)} case(s), {len(wanted)} placeholder(s), "
          f"{len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
