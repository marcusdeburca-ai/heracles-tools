# csv-col-stats

A read-only, standard-library Python tool that profiles each column of one or more CSV files. For every column it reports:

- filled vs. empty cells (and fill percentage)
- number of distinct values
- shortest and longest value length
- numeric min / max / mean / median (when every non-empty value is a number)
- the most common values

It also counts ragged rows (rows whose field count differs from the header). Short rows are treated as having empty trailing cells.

## Usage

```
python csv-col-stats.py data.csv
python csv-col-stats.py --top 5 a.csv b.csv
python csv-col-stats.py --delimiter ';' --json export.csv > profile.json
python csv-col-stats.py --columns email,country users.csv
python csv-col-stats.py --help
```

Options: `-d/--delimiter`, `-e/--encoding` (default `utf-8-sig`), `-n/--top`, `-c/--columns`, `--json`.

Exit status is 1 if any file could not be read or decoded, otherwise 0.

## Limitations

- Holds all distinct values per column in memory, so very large high-cardinality files may use a lot of RAM.
- Delimiter auto-detection is a heuristic; pass `-d` if it guesses wrong.
- Numeric detection uses Python `float()` (so `1e3` counts as numeric; thousands separators are only handled in simple cases like `1,234.5`).
- Values are whitespace-stripped before analysis.
- Does not modify, write, or delete any files, and makes no network calls.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
