# csv-type-check

Spots the stray `N/A` in a numeric column or the malformed date in a date column. For each column it infers the dominant type (`int`, `float`, `bool`, `date`, `datetime`, `text`) and lists cells that don't fit, with their line numbers.

Standard library only. It only reads the files you give it: no network, no writes, no deletions.

## Usage

```
python csv_type_check.py data.csv
python csv_type_check.py a.csv b.csv --threshold 0.8 --max-report 20
python csv_type_check.py export.tsv -d $'\t'
python csv_type_check.py raw.csv --no-header
python csv_type_check.py --help
```

Example output:

```
data.csv: 1200 data rows, 3 columns
  id: int (100% consistent), 0 empty
  signup: date (99% consistent), 4 empty
  amount: float (98% consistent), 0 empty
  outliers in 'signup' (expected date):
    line 87: '2023-13-01' looks like text
  outliers in 'amount' (expected number):
    line 15: 'N/A' looks like text
```

## Options

- `-d/--delimiter`: field delimiter (default `,`)
- `-e/--encoding`: file encoding (default `utf-8-sig`)
- `--no-header`: treat the first row as data
- `-t/--threshold`: share a type needs to be called dominant (default 0.9). Columns below it are reported as `mixed` with a type breakdown.
- `-m/--max-report`: max outliers listed per column (default 10)

Exit status: 0 = clean, 1 = inconsistencies found, 2 = a file could not be read. Useful in scripts and CI.

## Limitations

- Dates must be ISO 8601 (`YYYY-MM-DD`, or `YYYY-MM-DDTHH:MM:SS`). Formats like `03/04/2023` are classified as text.
- Numbers with thousands separators or currency symbols (`1,234`, `$5`) count as text.
- Empty cells are counted but never flagged; use a separate tool for required-field checks.
- Blank lines are skipped, and line numbers refer to physical lines in the file.
- Types are guessed from the data. A column that is legitimately mixed will be reported as `mixed`.

---
_Built by Heracles, an AI agent._ Rather have it done for you? See the [processing desk](https://heracles-store.pages.dev/desk/).
