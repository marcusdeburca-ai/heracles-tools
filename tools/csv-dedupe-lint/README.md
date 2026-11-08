# csv-dedupe-lint

A small standard-library-only CLI that lints CSV files for:

- duplicate rows (whole-row by default, or by a set of key columns)
- blank cells
- ragged rows (column count differs from the header)

It can also write a deduplicated copy to a new file.

## Usage

```sh
# Lint one file, whole-row duplicates
python csv_dedupe_lint.py data.csv

# Treat rows with the same id+email as duplicates
python csv_dedupe_lint.py --key id,email a.csv b.csv

# Write a cleaned copy (output must not already exist)
python csv_dedupe_lint.py --write-clean cleaned.csv data.csv

# Semicolon-separated files
python csv_dedupe_lint.py --delimiter ';' europe.csv

python csv_dedupe_lint.py --help
```

Exit status is `0` when no problems are found, `1` when problems are found, and `2` on usage errors.

## Limitations

- The first non-empty row is always treated as the header.
- Input is read as UTF-8 (a BOM is tolerated); other encodings are not supported.
- Only the first occurrence of a duplicate is kept when writing a clean copy; no fuzzy matching.
- Blank-cell and ragged-row checks do not remove or repair data; they only report it.
- Loads unique rows into memory, so very large files may use significant RAM.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
