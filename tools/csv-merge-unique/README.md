# csv-merge-unique

**Merge multiple CSV files that share the same header, deduplicate rows, and write a clean CSV.**  
All processing stays local, uses only the Python standard library, and never deletes files.

## Installation

Save the script as `csv-merge-unique` and make it executable:

```bash
chmod +x csv-merge-unique
```

## Usage

```bash
csv-merge-unique file1.csv file2.csv [file3.csv ...] [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-o FILE`, `--output FILE` | Write result to `FILE` instead of stdout. |
| `-d CHAR`, `--delimiter CHAR` | CSV field delimiter (default `,`). |
| `-q CHAR`, `--quotechar CHAR` | Quote character (default `"`). |
| `--skip-empty` | Skip rows where every field is empty. |
| `-h`, `--help` | Show help message. |

### Example

```bash
# Merge three CSVs, remove duplicates, and save to merged.csv
csv-merge-unique data1.csv data2.csv data3.csv -o merged.csv

# Pipe result to another command
csv-merge-unique a.csv b.csv | sort
```

## Limitations

* All input files must have **identical headers** (same columns in the same order).  
* Duplicate detection is exact; differing whitespace or quoting makes rows distinct.  
* Works only with text CSVs; binary data is not supported.

## License

Public domain / MIT – use as you wish.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
