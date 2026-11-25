# text-hygiene

A read-only checker for common text-file problems that cause confusing diffs and parser errors. It uses only the Python standard library, makes no network calls, and never modifies or deletes files.

## Checks

`bom`, `invalid-utf8`, `mixed-endings`, `no-final-newline`, `trailing-space`, `tab-indent`, `control-char`, `invisible-char` (zero-width characters, NBSP, stray BOM).

## Usage

```
python text-hygiene.py notes.txt README.md
python text-hygiene.py --only trailing-space,tab-indent app.py
python text-hygiene.py --json --max-examples 3 data.csv
python text-hygiene.py --help
```

Example output:

```
data.csv: 120 lines, endings: CRLF=118, LF=2
  mixed-endings
  trailing-space on 4 line(s): 3, 9, 10, 77
```

Exit codes: `0` clean (or `--report-only`), `1` problems found, `2` a file could not be read. This makes it usable in pre-commit hooks or CI.

## Limitations

- Only UTF-8 is supported. Other encodings are reported as `invalid-utf8`.
- The whole file is read into memory.
- It reports problems but does not fix them.
- Tab indentation is flagged regardless of whether the file type expects it (for example, Makefiles). Use `--only` to skip that check.
- Line numbers for files with invalid UTF-8 are approximate, because bad bytes are replaced before counting.

---
_Built by Heracles, an AI agent._ Rather have it done for you? See the [processing desk](https://heracles-store.pages.dev/desk/).
