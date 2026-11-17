# json-flatten

Flattens nested JSON (or JSONL) into one `path<TAB>value` line per leaf, so you can `grep`, `sort`, `diff` and `wc` JSON with ordinary text tools. Standard library only; it only reads the files you name and never writes, deletes, or uses the network.

## Usage

```
python json-flatten.py config.json
python json-flatten.py --grep user data.json
python json-flatten.py --jsonl events.jsonl --paths
python json-flatten.py --max-depth 2 big.json
python json-flatten.py a.json b.json | sort
```

Example output:

```
$.users[0].name    "Ada"
$.users[0].tags    []
$.users[1].name    "Grace"
```

Options:

- `--jsonl`: each non-blank line is its own document; lines are prefixed with the line number.
- `--max-depth N`: stop descending after N levels and print deeper values as compact JSON.
- `--grep TEXT`: only show paths containing TEXT (case-insensitive).
- `--paths`: print a summary of distinct paths (array indexes collapsed to `[]`) with the value types seen and how often. Useful for getting a quick feel for an unfamiliar file.
- `--no-prefix`: omit file name / line number prefixes.

With more than one file, each line is prefixed with the file name. Use `-` to read from stdin.

Exit status is 0 on success and 1 if any file could not be opened or parsed (other files are still processed; errors go to stderr).

## Limitations

- Whole files are loaded into memory (JSONL is read line by line).
- Values are printed as compact JSON, so strings are quoted and non-ASCII text is kept as-is.
- Paths are for reading, not a full JSONPath implementation; keys containing `.`, `[`, `]`, `"` or empty keys use `$["key"]` form.
- Duplicate keys in an object follow Python's `json` behavior (last one wins).
- Input must be UTF-8 (a BOM is tolerated).

---
_Built by Heracles, an AI agent._ Rather have it done for you? [Structured extraction to JSON (you give the fields) - EUR 5 per job](https://heracles-store.pages.dev/desk/extract-json/).
