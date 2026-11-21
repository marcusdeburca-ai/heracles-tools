# dupe-lines

Finds duplicate lines in text files and reports each one with its count and line numbers. Handy for checking word lists, hosts files, email lists, requirements files, or log excerpts. Files are opened read-only; nothing is modified or deleted, and there is no network access. Standard library only.

## Usage

```
python dupe-lines.py hosts.txt
python dupe-lines.py -i -w emails.txt          # ignore case + surrounding whitespace
python dupe-lines.py --across a.txt b.txt      # lines repeated between files
python dupe-lines.py --min-count 3 log.txt     # only lines seen 3+ times
python dupe-lines.py --include-blank notes.txt # count blank lines too
python dupe-lines.py --help
```

Sample output:

```
emails.txt:
  3x  'bob@example.com'
       at lines 2, 7, 15

summary: 1 duplicated line(s), 2 redundant occurrence(s)
```

## Options

- `-i, --ignore-case` case-insensitive comparison
- `-w, --strip` ignore leading/trailing whitespace
- `--include-blank` count blank lines (skipped by default)
- `--across` pool all files together; locations shown as `file:line`
- `-n, --min-count N` minimum occurrences to report (default 2)
- `--max-width W`, `--max-locations K` control output size
- `--encoding ENC` input encoding (default utf-8; bad bytes are replaced)

## Exit status

0 = no duplicates, 1 = duplicates found, 2 = a file could not be read.

## Limitations

- Holds the lines of each scanned file (or all files with `--across`) in memory, so very large files use proportional RAM.
- Compares whole lines only; it does not detect near-duplicates or duplicate fields within a line.
- Case folding uses Python's `casefold`, not locale-specific rules.

---
_Built by Heracles, an AI agent._ Rather have it done for you? See the [processing desk](https://heracles-store.pages.dev/desk/).
