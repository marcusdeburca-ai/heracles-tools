#!/usr/bin/env python3
"""
csv-blank-scan: A tool to detect missing data in CSV files.

It scans for empty strings, 'NaN', 'NULL', or whitespace-only values in cells.
"""

import argparse
import csv
import sys
from collections import defaultdict

# Common representations of missing data
MISSING_TOKENS = {
    "", "nan", "null", "none", "na", "n/a", "nil", "missing", "-"
}

def is_missing(value):
    """Check if a cell value represents missing data."""
    if value is None:
        return True
    # Strip whitespace and check against known tokens
    stripped = value.strip().lower()
    return stripped in MISSING_TOKENS

def scan_csv(filepath, check_all_cols, specific_cols):
    """Scan a CSV file for missing values."""
    try:
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                print(f"[{filepath}] Warning: No headers found.", file=sys.stderr)
                return 0

            headers = reader.fieldnames
            # Determine which columns to check
            if check_all_cols:
                cols_to_check = headers
            else:
                cols_to_check = specific_cols
                # Validate that requested columns exist
                missing_cols = [c for c in cols_to_check if c not in headers]
                if missing_cols:
                    print(f"[{filepath}] Error: Columns not found: {', '.join(missing_cols)}", file=sys.stderr)
                    return 1

            stats = {col: 0 for col in cols_to_check}
            total_rows = 0
            rows_with_missing = 0

            for row_num, row in enumerate(reader, start=2): # Start at 2 (1 is header)
                total_rows += 1
                row_has_missing = False
                
                for col in cols_to_check:
                    # Handle case where row is shorter than header (ragged)
                    val = row.get(col)
                    if val is None or is_missing(val):
                        stats[col] += 1
                        row_has_missing = True
                
                if row_has_missing:
                    rows_with_missing += 1

            # Output results
            print(f"File: {filepath}")
            print(f"Total Rows: {total_rows}")
            print(f"Rows with at least one missing value: {rows_with_missing}")
            print("-" * 40)
            
            # Sort by count of missing values descending
            sorted_cols = sorted(cols_to_check, key=lambda c: stats[c], reverse=True)
            
            for col in sorted_cols:
                count = stats[col]
                if count > 0:
                    pct = (count / total_rows * 100) if total_rows > 0 else 0
                    print(f"  {col}: {count} missing ({pct:.2f}%)")
            
            if all(stats[c] == 0 for c in cols_to_check):
                print("  No missing values found in checked columns.")
            
            return 0

    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error processing {filepath}: {e}", file=sys.stderr)
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Scan CSV files for missing/blank values in rows or specific columns.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.csv
  %(prog)s data.csv --columns name, age
  %(prog)s *.csv --all
        """
    )
    
    parser.add_argument(
        'files',
        nargs='+',
        help='CSV file(s) to scan.'
    )
    
    parser.add_argument(
        '-c', '--columns',
        nargs='+',
        help='Specific column names to check. If omitted, checks all columns.'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Force check of all columns (overrides -c if both are provided? No, -c takes precedence if specified). '
             'Actually, if -c is not provided, it defaults to all. This flag is for clarity.'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed info per row (not implemented in this simple version, placeholder for future).'
    )

    args = parser.parse_args()

    if args.verbose:
        print("Verbose mode is a placeholder in this version.", file=sys.stderr)

    # Logic: If specific columns are provided, use them. Otherwise, use all.
    if args.columns:
        specific_cols = args.columns
        check_all = False
    else:
        specific_cols = []
        check_all = True

    exit_code = 0
    for file in args.files:
        if not file.lower().endswith('.csv'):
            print(f"Warning: Skipping {file} (not a .csv extension)", file=sys.stderr)
            continue
        
        result = scan_csv(file, check_all, specific_cols)
        if result != 0:
            exit_code = result

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
