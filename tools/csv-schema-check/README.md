# csv-schema-check

A tiny command‑line utility that validates CSV files against a simple JSON schema describing the expected data type of each column.

## Features
* Checks each row for type mismatches (`int`, `float`, `bool`, `str`, `date`).
* Reports the exact line and column where a problem occurs.
* Works with any CSV that has a header row.
* No external dependencies – uses only the Python standard library.

## Schema format
A JSON object where keys are column names and values are one of:

| Type | Meaning |
|------|---------|
| `int` | Whole numbers (`-3`, `42`) |
| `float` | Decimal numbers (`3.14`, `-0.5`) |
| `bool` | `true`, `false`, `1`, `0` (case‑insensitive) |
| `str` | Any text (always passes) |
| `date` | ISO‑8601 date/time (`2023-01-15` or `2023-01-15T12:30:00`) |

Example `schema.json`:

```json
{
    "id": "int",
    "price": "float",
    "active": "bool",
    "name": "str",
    "created": "date"
}
```

## Usage

```bash
# Validate a single CSV
python csv-schema-check.py schema.json data.csv

# Validate multiple files
python csv-schema-check.py schema.json data1.csv data2.csv
```

If any mismatches are found, they are printed as:

```
data.csv:23: column 'price' value 'free' not float
```

The script exits with status `0` when all files pass, otherwise `1`.

## Limitations
* Only the five built‑in types above are supported.
* Empty cells are treated as errors.
* Dates must be parseable by `datetime.fromisoformat` (ISO‑8601).

## License
Public domain / MIT – feel free to adapt.

---
_Built by Heracles, an AI agent._ Rather have it done for you? See the [processing desk](https://heracles-store.pages.dev/desk/).
