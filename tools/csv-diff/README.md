# csv-diff

Compare two CSV files by one or more key columns and see exactly what changed: rows added, rows removed, cells changed, and columns added or dropped. Handy for checking an export against last week's, or verifying a cleanup script did only what you expected.

Python 3, standard library only. Read-only: it never writes, deletes, or touches the network.

## Usage

```
python csv-diff.py old.csv new.csv --key id
python csv-diff.py a.csv b.csv --key first,last --ignore updated_at
python csv-diff.py a.csv b.csv --key id --format json > diff.json
python csv-diff.py a.tsv b.tsv --key id --delimiter '\t' --trim
python csv-diff.py --help
```

Options: `--key/-k` (required), `--delimiter/-d`, `--ignore/-i`, `--trim`, `--format/-f text|json`, `--limit/-n`.

Exit codes: `0` no differences, `1` differences found, `2` usage or input error. This makes it usable in scripts and CI.

## Example output

```
Rows added (1):
  id='4'
Rows changed (1):
  id='2' | price: '9.99' -> '10.49'
Summary: 1 added, 0 removed, 1 changed, 1 unchanged
```

## Limitations

- Files are loaded fully into memory.
- Rows are matched by key only; row order is ignored.
- If a key appears more than once in a file, only the first row is compared and the duplicates are reported.
- Cell comparison is exact string comparison (use `--trim` to ignore surrounding whitespace). No numeric or date normalization.
- Input must be UTF-8 (a BOM is accepted).
- Only columns present in both files are compared for cell changes.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
