# csv-blank-scan

A lightweight command-line tool to audit CSV files for missing data. It identifies rows or specific columns that contain empty strings, `NaN`, `NULL`, or other common "missing" tokens.

## Usage

```bash
python csv-blank-scan.py data.csv
```

### Check Specific Columns

```bash
python csv-blank-scan.py data.csv --columns name, email, age
```

### Multiple Files

```bash
python csv-blank-scan.py *.csv
```

## Features

- **Smart Missing Detection**: Treats `""`, `"nan"`, `"null"`, `"none"`, `"na"`, `"n/a"`, `"nil"`, `"missing"`, and `"-"` (case-insensitive, trimmed) as missing.
- **Column-Specific**: You can choose to audit all columns or just specific ones.
- **Statistics**: Reports total missing counts per column and the percentage of rows affected.
- **Safe**: Read-only, no network access, no file modification.

## Limitations

- Assumes the first row is the header.
- Does not handle complex multi-line fields within a single cell (standard CSV parsing applies).
- Only detects textual representations of missing data; it does not infer missing data from context (e.g., zeros or dates).

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
