# csv-cleaner

`csv-cleaner` is a lightweight command‑line tool that:
* trims leading/trailing whitespace from every cell
* removes duplicate rows (after trimming)
* optionally preserves the first row as a header

It works purely on the local filesystem, never accesses the network, and keeps the original files intact unless you explicitly overwrite them.

## Installation

Simply copy the file to a directory on your `PATH` and make it executable:

```bash
chmod +x csv-cleaner
sudo mv csv-cleaner /usr/local/bin/
```

## Usage

```bash
# Clean a single file in place
csv-cleaner data.csv

# Write output to a new file
csv-cleaner -o cleaned.csv data.csv

# Clean multiple files, preserving the header row
csv-cleaner -s file1.csv file2.csv

# Clean a directory of CSVs, outputting to another directory
csv-cleaner -o cleaned/ *.csv
```

## Limitations

* Only standard CSV format is supported (comma delimiter, double‑quote quoting).
* Does not handle very large files that exceed memory; it loads the entire file into memory.
* Only removes exact duplicate rows after trimming; it does not reorder rows.
* No support for custom delimiters or quoting styles.

Happy cleaning!

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
