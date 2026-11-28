# jsonl-compact

A small CLI tool to validate and compact JSON Lines (JSONL) files.

## Features
- Validates each line as JSON.
- Outputs compact JSON (no extra whitespace) to stdout.
- Reports invalid lines to stderr with line numbers.
- Skips blank lines.
- Exits with code 1 if any lines are invalid.

## Usage
```bash
# Compact and validate a JSONL file
jsonl-compact input.jsonl > output.jsonl

# Skip invalid lines (continue processing even if errors found)
jsonl-compact --skip-invalid input.jsonl > output.jsonl

# Quiet mode (no stderr output, only stdout JSON)
jsonl-compact --quiet input.jsonl > output.jsonl
```

## Limitations
- Only handles line-delimited JSON (JSONL).
- Does not modify the input file.
- Large files are read into memory entirely.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [Structured extraction to JSON (you give the fields) - EUR 5 per job](https://heracles-store.pages.dev/desk/extract-json/).
