# csv-header-check

A tiny command‑line utility that verifies every data row in a CSV file has the same number of columns as the header row.

## Features

* Detect rows with too few or too many fields.
* Auto‑detects common delimiters (comma, tab, semicolon, pipe) or lets you specify one.
* Optionally ignore extra empty trailing fields (`--ignore-trailing`).
* Works on one or many files; never modifies or deletes anything.
* No external dependencies – only the Python standard library.

## Installation

Save the single file `csv-header-check.py` and make it executable:

```bash
chmod +x csv-header-check.py
```

## Usage

```bash
# Basic check (auto‑detect delimiter)
./csv-header-check.py data.csv

# Check multiple files
./csv-header-check.py *.csv

# Specify a delimiter explicitly
./csv-header-check.py -d ';' data_semicolon.csv

# Ignore extra empty fields at the end of rows
./csv-header-check.py -i data.csv

# Quiet mode – only a summary printed to stderr
./csv-header-check.py -q data.csv
```

### Output

* For each problematic row it prints `filename:line: expected N fields, got M`.
* After each file it reports `good rows, problematic rows`.
* A non‑zero exit status (1) indicates at least one mismatched row.

## Limitations

* Only validates column count, not data types or content.
* Delimiter detection is heuristic and may fail on exotic formats.
* Does not handle quoted newlines beyond what `csv.reader` supports.

## License

Public domain / MIT‑compatible – feel free to copy and adapt.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
