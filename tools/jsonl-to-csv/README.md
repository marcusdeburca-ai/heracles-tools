# jsonl-to-csv

Converts JSON Lines files (one JSON object per line) into a CSV. Columns are the union of all keys across all input files, in first-seen order, so records with differing keys still line up. Malformed or non-object lines are reported with `file:line` on stderr and skipped.

## Usage

```
python jsonl-to-csv.py events.jsonl > events.csv
python jsonl-to-csv.py a.jsonl b.jsonl -o merged.csv
python jsonl-to-csv.py logs.jsonl --flatten --columns id,user.name,status
python jsonl-to-csv.py --help
```

Options: `-o/--output`, `-c/--columns`, `--flatten`, `--strict`, `--no-header`.

Exit codes: 0 success, 1 some lines skipped, 2 usage/file error.

## Behavior

- `null` becomes an empty cell; booleans become `true`/`false`.
- Nested objects and arrays are written as compact JSON, or expanded into dotted columns with `--flatten` (arrays are still JSON).
- `-o` refuses to overwrite an existing file. The tool never deletes anything and makes no network calls.

## Limitations

- Loads all records into memory (needs two passes to discover columns).
- Input must be UTF-8 (a BOM is accepted).
- Only one object per line; pretty-printed multi-line JSON is not supported.
- With `--flatten`, a key literally containing a dot may collide with a nested key.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
