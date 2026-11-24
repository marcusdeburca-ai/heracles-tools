# json-key-case

Converts every object key in JSON or JSONL files (recursively, including objects inside arrays) to `snake`, `camel`, `pascal` or `kebab` case. Output goes to stdout; input files are only read, never changed. Standard library only, no network.

## Usage

```
python json-key-case.py --to snake api.json > api_snake.json
python json-key-case.py --to camel --indent 0 user.json
python json-key-case.py -t kebab events.jsonl
python json-key-case.py --help
```

Word splitting understands `camelCase`, `PascalCase`, acronyms (`HTTPServer` -> `http_server`), and `-`, `_`, space or other separators.

## Exit codes

- `0` success
- `1` file unreadable or invalid JSON
- `2` key collisions (e.g. `userId` and `user_id` both become `user_id`); the first value is kept, later ones dropped, and each collision is reported on stderr

## Limitations

- Only keys change; string values are untouched.
- Case conversion is lossy: `user_ID2` and similar may not round-trip.
- Keys with no letters or digits (e.g. `"---"`) are left as-is.
- Duplicate keys within the original JSON are resolved by Python's `json` (last wins) before conversion.
- Output is written to stdout only; multiple files are printed one after another.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [Structured extraction to JSON (you give the fields) - EUR 5 per job](https://heracles-store.pages.dev/desk/extract-json/).
