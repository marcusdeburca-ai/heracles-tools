# json-dupkeys

Finds duplicate keys inside JSON objects. Python's `json` module (and many other parsers) silently keep only the last value for a repeated key, so mistakes like a pasted-twice `"timeout"` in a config go unnoticed. `json-dupkeys` reports each one with its JSON path and says whether the values are identical or conflicting.

Standard library only, read-only, no network access.

## Usage

```
python json-dupkeys.py config.json
python json-dupkeys.py a.json b.json
python json-dupkeys.py --jsonl events.jsonl
cat data.json | python json-dupkeys.py -
python json-dupkeys.py --help
```

Example output:

```
config.json: $.server: key "port" appears 2 times (CONFLICTING values, last wins: 8081)
config.json: $.items[2]: key "id" appears 2 times (identical values)
```

Options:

- `--jsonl` treats each non-blank line as its own JSON document (reports `file:line`).
- `-q`, `--quiet` prints only the summary and errors.

Exit codes: `0` no duplicates, `1` duplicates found, `2` a file could not be read or parsed (takes precedence). The summary goes to stderr, so stdout holds only findings.

## Limitations

- Reports JSON paths, not line numbers (except the line of each document in `--jsonl` mode).
- Keys are compared after JSON unescaping, so `"a"` and `"\u0061"` count as duplicates (correct per the spec's semantics, but possibly surprising).
- Loads each file fully into memory; very deep nesting may hit Python's recursion limit and be reported as an error.
- Only strict JSON is accepted (no comments or trailing commas). A UTF-8 BOM is tolerated.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [Structured extraction to JSON (you give the fields) - EUR 5 per job](https://heracles-store.pages.dev/desk/extract-json/).
