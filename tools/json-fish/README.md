# json-fish

Extracts and validates JSON embedded in messy text. Handy for LLM replies that wrap JSON in prose or markdown fences, or for logs with JSON payloads mixed into plain lines. Every candidate is parsed with Python's real JSON parser, so only valid JSON comes out.

Standard library only, a single file, no network access. Input files are only read, never modified or deleted.

## Usage

```
python json-fish.py reply.txt                    # pretty-print every JSON value found
python json-fish.py --first --only objects a.md  # first JSON object in each file
python json-fish.py --jsonl logs/*.txt           # one compact value per line
python json-fish.py --get user.tags.0 reply.txt  # select a nested field
python json-fish.py --locations reply.txt        # report file:line on stderr
cat reply.txt | python json-fish.py -            # read from stdin
```

Options: `--only {any,objects,arrays}`, `--min-items N`, `--get PATH`, `--first`, `--jsonl`, `--indent N`, `--sort-keys`, `--locations`. Run with `--help` for details.

Exit codes: `0` found something, `1` nothing found, `2` a file could not be read.

## Limitations

- Strict JSON only: single quotes, trailing commas, comments, and `NaN`-style repairs are not attempted. Python's parser does accept `NaN` and `Infinity`.
- Top-level scalars (bare strings or numbers) are ignored; only objects and arrays are extracted.
- Short bracketed text like `[1]` in prose is valid JSON and will match. Use `--only objects` or `--min-items` to filter.
- Nested values are reported once as part of the outermost value, not separately.
- Files are read fully into memory, so it is not meant for multi-gigabyte inputs.
- `--get` paths use `.` as a separator, so keys containing dots can't be selected.

_Built by Heracles, an AI agent._
