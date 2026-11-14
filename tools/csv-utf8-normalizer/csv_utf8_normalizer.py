#!/usr/bin/env python3
"""
csv-utf8-normalizer: Detect and fix encoding issues in CSV files.

This tool reads a CSV file, detects its encoding (using chardet-like heuristics
from the standard library's codecs), and writes a normalized UTF-8 version.
It specifically handles:
1. UTF-8 BOM removal.
2. Windows-1252 (Latin-1) to UTF-8 conversion.
3. ASCII to UTF-8 (no-op but ensures consistency).

Usage:
    python csv-utf8-normalizer.py input.csv [output.csv]
    python csv-utf8-normalizer.py input.csv --check
"""

import argparse
import sys
import os
import codecs
from typing import Tuple


def detect_encoding(data: bytes) -> str:
    """
    Detect the encoding of a byte string using a simple heuristic.
    Returns the encoding name.
    """
    # Check for UTF-8 BOM
    if data.startswith(codecs.BOM_UTF8):
        return 'utf-8-sig'
    
    # Check for UTF-16 LE/BE BOM
    if data.startswith(codecs.BOM_UTF16_LE):
        return 'utf-16-le'
    if data.startswith(codecs.BOM_UTF16_BE):
        return 'utf-16-be'

    # Try UTF-8 first (most common web standard)
    try:
        data.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        pass

    # Try Latin-1 (Windows-1252 is a superset, but Latin-1 always works for bytes)
    # Note: Python's 'latin-1' maps bytes 1:1 to Unicode code points.
    # For better accuracy on Windows-1252 specific chars (like curly quotes),
    # we could try 'cp1252' first.
    try:
        data.decode('cp1252')
        return 'cp1252'
    except UnicodeDecodeError:
        pass

    # Fallback to Latin-1 which never fails
    return 'latin-1'


def normalize_csv(input_path: str, output_path: str = None, check_only: bool = False) -> Tuple[bool, str]:
    """
    Normalize a CSV file to UTF-8.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not os.path.exists(input_path):
        return False, f"Error: File '{input_path}' does not exist."

    try:
        with open(input_path, 'rb') as f:
            raw_data = f.read()
    except IOError as e:
        return False, f"Error reading file: {e}"

    detected_encoding = detect_encoding(raw_data)
    
    # If it's already UTF-8 (without BOM), and check_only, we can report it's clean.
    # If it has BOM, we consider it 'needs fixing' for strict UTF-8 no-BOM.
    is_already_clean = (detected_encoding == 'utf-8')
    
    if check_only:
        if is_already_clean:
            return True, f"OK: File is already UTF-8 (no BOM)."
        else:
            return True, f"INFO: File detected as {detected_encoding}. Normalization recommended."

    # Decode using detected encoding
    try:
        text_content = raw_data.decode(detected_encoding)
    except UnicodeDecodeError as e:
        return False, f"Error decoding file with {detected_encoding}: {e}"

    # If it was UTF-8 with BOM, the decode('utf-8-sig') strips it.
    # If it was cp1252 or latin-1, we now have proper Unicode.
    
    # Prepare output
    if output_path is None:
        # If no output specified, we can't overwrite safely without backup or explicit flag.
        # For this tool, we require output path if not check_only, OR we can support in-place?
        # The prompt says "never delete files". In-place write overwrites. 
        # Most CLI tools require explicit output or a --in-place flag.
        # Let's stick to requiring output_path to be safe, or default to <input>_utf8.csv?
        # Let's default to <input>_utf8.csv if not provided.
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_utf8{ext}"

    # Encode to UTF-8 (no BOM)
    utf8_bytes = text_content.encode('utf-8')

    # Write output
    try:
        with open(output_path, 'wb') as f:
            f.write(utf8_bytes)
    except IOError as e:
        return False, f"Error writing file: {e}"

    return True, f"Success: Converted {detected_encoding} to UTF-8. Output: {output_path}"


def main():
    parser = argparse.ArgumentParser(
        description="Normalize CSV files to UTF-8 (removes BOM, converts Latin-1/CP1252)."
    )
    parser.add_argument(
        "input",
        help="Path to the input CSV file."
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Path to the output CSV file. If omitted, defaults to <input>_utf8.csv."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check the encoding and report status. Do not write a new file."
    )

    args = parser.parse_args()

    success, message = normalize_csv(args.input, args.output, args.check)

    print(message)
    
    # Exit code 0 for success or info, 1 for error
    if "Error" in message:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
