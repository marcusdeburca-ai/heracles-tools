#!/usr/bin/env python3
"""
jsonl-compact: Validates and compacts JSON Lines (JSONL) files.

Reads a JSONL file, validates each line as JSON, and writes valid JSON
records to stdout in a compact format (no whitespace). Invalid lines are
reported to stderr with line numbers.
"""

import argparse
import json
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate and compact JSON Lines (JSONL) files.",
        epilog="Example: jsonl-compact data.jsonl > clean.jsonl"
    )
    parser.add_argument(
        "input",
        help="Path to the input JSONL file."
    )
    parser.add_argument(
        "-s",
        "--skip-invalid",
        action="store_true",
        help="Skip invalid lines instead of exiting on first error."
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress error messages to stderr (only output valid JSON)."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    valid_count = 0
    invalid_count = 0
    first_error = False

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        try:
            # Parse and re-serialize to compact form
            data = json.loads(stripped)
            compact = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            print(compact)
            valid_count += 1
        except json.JSONDecodeError as e:
            invalid_count += 1
            if not args.quiet:
                print(f"Line {i}: Invalid JSON - {e}", file=sys.stderr)
                if not first_error:
                    first_error = True

        if invalid_count > 0 and not args.skip_invalid and not args.quiet:
            # If not skipping invalid, we still process all but exit non-zero
            pass

    if invalid_count > 0:
        if not args.quiet:
            print(f"Done: {valid_count} valid, {invalid_count} invalid lines.", file=sys.stderr)
        sys.exit(1)
    else:
        if not args.quiet:
            print(f"Done: {valid_count} valid lines.", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
