# csv-grep

Like `grep`, but column-aware: print the rows of a CSV file whose fields match
regular expressions. Input files are only read, never modified or deleted, and
nothing touches the network. Python 3, standard library only.

## Usage

```
python csv_grep.py -c COLUMN=REGEX [-c ...] [options] FILE [FILE ...]
```

Examples:

```
# failed or errored jobs
python csv_grep.py -c "status=^(failed|error)$" jobs.csv

# AND of two conditions
python csv_grep.py -c "email=@example\.com$" -c plan=pro users.csv

# OR, case-insensitive
python csv_grep.py --any -i -c city=paris -c city=berlin people.csv

# rows where 'note' is not empty
python csv_grep.py -v -c "note=^$" data.csv

# semicolon-delimited, column referenced by number, count only
python csv_grep.py --count -d ";" -c "3=^2024" export.csv
```

Options: `-c/--cond`, `--any`, `-v/--invert`, `-i/--ignore-case`,
`-d/--delimiter` (`\t` for tabs), `--count`, `-h/--help`.

Output goes to stdout with a single header line (even for multiple files), so
you can redirect it into a new file.

Exit codes: `0` rows matched, `1` no rows matched, `2` error.

## Limitations

- Regexes use Python `re.search` (unanchored); add `^`/`$` to anchor.
- Columns are matched by exact header name, or by 1-based number if no header
  has that name.
- All files must share the same header as the first file; others are skipped
  with a warning.
- Short rows are treated as having empty strings in missing cells.
- Input is read as UTF-8 (a BOM is tolerated); output is always UTF-8 with `\n`
  line endings. Quoting in output follows Python's `csv` defaults.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
