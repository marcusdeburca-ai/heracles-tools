# json-shape

Summarizes the structure of JSON or JSONL files: every path, the types seen there, how many times it occurs, and how often a key is present in its parent object. Paths with inconsistent types (e.g. a field that is sometimes a string and sometimes a number) are flagged `MIXED`; keys missing from some objects are flagged `optional`.

Standard library only. Read-only: it never writes, deletes, or uses the network.

## Usage

```
python json_shape.py data.json
python json_shape.py --jsonl events.jsonl --strict
python json_shape.py a.json b.json --max-depth 3 --format json
```

Sample output:

```
PATH         TYPES                          COUNT  PRESENT  FLAGS
$            object                             3
id           integer                            3  3/3
tags         array                              2  2/3      optional
tags[]       string                             5
age          null|string                        3  3/3      MIXED
```

Options: `--jsonl`, `--max-depth N`, `--format text|json`, `--strict`.

Exit codes: `0` ok, `1` mixed types found with `--strict`, `2` a file could not be read or parsed.

## Limitations

- Multiple files are merged into a single summary, not reported per file.
- `integer` and `number` together are not treated as mixed; `null` plus one other type is also not mixed.
- Keys containing `.` or `[]` can make paths ambiguous.
- The whole of each non-JSONL file is loaded into memory.
- Presence counts for keys inside arrays of objects are relative to all objects at that array path.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [Structured extraction to JSON (you give the fields) - EUR 5 per job](https://heracles-store.pages.dev/desk/extract-json/).
