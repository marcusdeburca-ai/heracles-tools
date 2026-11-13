# csv-normalizer

A tiny command‑line utility that cleans and normalises CSV files.

## What it does

* **Trim whitespace** – leading and trailing spaces are removed from every field.
* **Remove empty rows** – rows that become completely blank after trimming are dropped.
* **Optional column‑count enforcement** – with `-e/--enforce-columns` rows whose number of columns differs from the header are discarded.
* Writes the cleaned CSV to **stdout** (or to a file with `-o`).

The tool never modifies the original files and never accesses the network.

## Installation

Copy the single file `csv_normalizer.py` somewhere in your `$PATH` and make it executable:

```bash
chmod +x csv_normalizer.py
mv csv_normalizer.py /usr/local/bin/csv-normalizer
```

## Usage

```bash
csv-normalizer data1.csv data2.csv > cleaned.csv
```

### Options

| Option | Description |
|--------|-------------|
| `-d`, `--delimiter` | Field delimiter (default `,`). |
| `--dialect` | CSV dialect understood by Python's `csv` module (default `excel`). |
| `-e`, `--enforce-columns` | Drop rows whose column count differs from the header. |
| `-o`, `--output` | Write combined output to the given file instead of stdout. |
| `-h`, `--help` | Show help message. |

### Example with column enforcement

```bash
csv-normalizer -e -o clean.csv messy.csv
```

Rows that have too few or too many columns compared to the header are omitted.

## Limitations

* Only works with text CSV files (no binary mode handling).
* Does not support streaming very large files beyond available memory (it reads each file into memory once).
* The dialect must be one of those provided by Python's standard `csv` module.

## License

Public domain / MIT – feel free to adapt.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
