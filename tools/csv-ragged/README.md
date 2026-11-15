# csv-ragged

Checks CSV files for "ragged" rows, meaning rows whose number of fields differs from the header. Reports the line numbers, how many rows are too short or too long, and a histogram of field counts. Optionally writes a repaired copy.

Standard library only. It never touches the network, never modifies or deletes inputs, and refuses to overwrite an existing output file.

## Usage

```
python csv-ragged.py data.csv
python csv-ragged.py a.csv b.csv -d ';' --max-report 50
python csv-ragged.py data.csv --fix data.fixed.csv
python csv-ragged.py data.csv --fix data.fixed.csv --truncate
python csv-ragged.py --help
```

Exit codes: `0` all rows match, `1` ragged rows found, `2` error (usable in scripts and CI).

## Options

- `-d/--delimiter`: delimiter (auto-detected among `, ; tab |` by default)
- `-e/--encoding`: input encoding (default `utf-8-sig`)
- `--max-report N`: how many bad rows to list per file
- `--fix OUT`: write a repaired copy (single input only). Short rows are padded with empty fields.
- `--truncate`: with `--fix`, cut over-long rows to the header width. This discards data.

## Limitations

- Line numbers refer to the end of the record, so multi-line quoted fields are reported at their last line.
- Without `--truncate`, over-long rows are copied unchanged into the fixed file, so it may still contain ragged rows. Re-run the tool on it to check.
- Blank lines are skipped, and the repaired copy drops them.
- Delimiter auto-detection is a heuristic. Pass `-d` if it guesses wrong.
- The repaired file is written as UTF-8 with the input's detected or given delimiter, and quoting may be normalized.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
