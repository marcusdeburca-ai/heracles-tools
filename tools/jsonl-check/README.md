# jsonl-check

A small, standard-library-only Python tool that validates JSON Lines (`.jsonl` / `.ndjson`) files before you load them into a pipeline.

## What it checks

- Each line parses as JSON (reports line number and reason)
- Duplicate keys within an object (which Python's `json` would otherwise silently collapse)
- Non-standard constants such as `NaN` and `Infinity`
- Required keys present (`--require id,ts`)
- Optional: non-object lines (`--object-only`) and blank lines (`--no-blank`)
- Keys whose values switch types across lines, e.g. `age` is sometimes a number and sometimes a string (`null` is ignored for this check)

It only reads the files you pass in. It never modifies or deletes anything and never uses the network.

## Usage

```
python jsonl-check.py events.jsonl
python jsonl-check.py --require id,timestamp logs/*.jsonl
python jsonl-check.py --object-only --strict-types --show-keys data.jsonl
cat data.jsonl | python jsonl-check.py -
python jsonl-check.py --help
```

Example output:

```
events.jsonl: 5 lines, 3 valid, 1 invalid, 1 blank, 1 missing required
  line 2: invalid JSON (Expecting value)
  line 4: missing required key(s): id
  mixed types for 'age': number=2, string=1
```

## Exit status

- `0` clean
- `1` problems found (invalid lines, missing required keys, or mixed types with `--strict-types`)
- `2` a file could not be read

## Limitations

- Type consistency is checked only on top-level keys, not nested ones.
- Integers and floats are both reported as `number`.
- Files are read as UTF-8 (a BOM is tolerated); undecodable bytes are replaced rather than reported.
- Does not validate against a full JSON Schema.
- Pretty-printed (multi-line) JSON is not supported, since each line must be a complete value.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [Structured extraction to JSON (you give the fields) - EUR 5 per job](https://heracles-store.pages.dev/desk/extract-json/).
