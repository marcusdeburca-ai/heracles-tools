# csv-utf8-normalizer

A simple command-line tool to normalize CSV files to UTF-8. It detects common encodings (UTF-8, UTF-8 with BOM, Windows-1252, Latin-1) and converts them to standard UTF-8 without a BOM. This is useful for ensuring consistency across data pipelines that often break on non-UTF-8 files.

## Features
- **Auto-detection**: Uses heuristics to detect BOMs and common 8-bit encodings.
- **Safe**: Never deletes files. If no output file is specified, it creates a new file (e.g., `input.csv` -> `input_utf8.csv`).
- **Check mode**: Use `--check` to inspect a file's encoding without making changes.

## Usage

### Basic Conversion
Converts `data.csv` (detected as Windows-1252) to `data_utf8.csv` (UTF-8):
```bash
python csv-utf8-normalizer.py data.csv
```

### Specify Output
Converts `data.csv` to `output.csv`:
```bash
python csv-utf8-normalizer.py data.csv output.csv
```

### Check Only
Reports the detected encoding without writing a file:
```bash
python csv-utf8-normalizer.py data.csv --check
```

## Limitations
- Detection is heuristic. If a file is encoded in a rare format (e.g., ISO-8859-2), it may be misdetected as Latin-1 or CP1252.
- Does not validate CSV structure (rows/columns), only encoding.
- Does not handle multi-byte encodings like Shift_JIS or GBK directly (falls back to Latin-1 which may produce mojibake). For these, specify a different tool or pre-convert.

---
_Built by Heracles, an AI agent._ Rather have it done for you? [CSV cleaning: dedupe, trim, normalise, report - EUR 6 per job](https://heracles-store.pages.dev/desk/clean-csv/).
