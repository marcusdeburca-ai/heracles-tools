# csv-audit

A single-file, standard-library Python tool that audits CSV files for common problems and can write a cleaned copy.

## What it checks

- Duplicate or blank header names
- Blank rows
- Ragged rows (field count differs from the header)
- Cells with leading/trailing whitespace
- Exact duplicate rows
- Columns that are entirely empty

## Usage

```
python csv_audit.py data.csv
python csv_audit.py a.csv b.csv -n 10
python csv_audit.py export.csv -d ";" -e latin-1
python csv_audit.py data.csv --clean cleaned/
python csv_audit.py --help
```

Example output:

```
data.csv: 120 data rows, 6 columns, delimiter ','
  blank row: 2 - line(s) 14, 57
  ragged row (header has 6 fields): 1 - line(s) 33
  duplicate row: 3 - line(s) 40, 41, 90
```

Exit status: `0` no issues, `1` issues found, `2` a file could not be read. This makes it usable in scripts and CI.

## Cleaning

`--clean DIR` writes `<name>.clean.csv` into `DIR` (created if needed). The cleaned copy has whitespace stripped, blank and exact-duplicate rows dropped, and short rows padded with empty fields. Rows with too many fields are left out of the copy and reported in the audit. The tool never modifies input files, never deletes anything, never overwrites an existing output file, and never uses the network.

## Limitations

- Delimiter auto-detection is a heuristic; use `-d` if it guesses wrong.
- The whole file is loaded into memory.
- Duplicate detection is exact (case-sensitive) after whitespace stripping.
- Cleaned output is always UTF-8 with `\n` line endings.
- Line numbers refer to the line where a record ends, which matters for multi-line quoted fields.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
