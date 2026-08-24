#!/usr/bin/env python3
"""
Replace the fileNames list in RunItems.py with the contents of filenames.txt.
"""

import sys
import os

FILENAMES_FILE = "fileslist_Neutrino_E-10_gun.txt"
RUNITEMS_FILE = "RunIISummer20UL17DIGIPremix_cfg.py"

def read_filenames(path):
    """Read non‑empty lines from the file, strip whitespace."""
    try:
        with open(path, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {path} not found.", file=sys.stderr)
        sys.exit(1)

def build_new_assignment(filenames):
    """Build the new line: process.mixData.input.fileNames = cms.untracked.vstring([...])"""
    # Use repr() to safely quote each filename (handles quotes and special chars)
    list_str = "[" + ", ".join(repr(f) for f in filenames) + "]"
    return f"process.mixData.input.fileNames = cms.untracked.vstring({list_str})"

def replace_in_file(file_path, old_prefix, new_line,filenames):
    """Replace the line that starts with old_prefix (after stripping) with new_line."""
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: {file_path} not found.", file=sys.stderr)
        sys.exit(1)

    found = False
    for i, line in enumerate(lines):
        # Compare stripped line to handle varying indentation
        if line.strip().startswith(old_prefix):
            # Preserve the original indentation
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = indent + new_line + "\n"
            found = True
            break

    if not found:
        print(f"Warning: No line starting with '{old_prefix}' found in {file_path}.", file=sys.stderr)
        print("No changes made.")
        return

    # Write back the modified content
    with open(file_path, "w") as f:
        f.writelines(lines)
    print(f"Successfully updated {file_path} with {len(filenames)} file names.")

def main():
    filenames = read_filenames(FILENAMES_FILE)
    if not filenames:
        print("Warning: No file names found in filenames.txt. Nothing to do.")
        sys.exit(0)

    new_line = build_new_assignment(filenames)
    # The prefix we look for (after stripping leading/trailing spaces)
    prefix = "process.mixData.input.fileNames ="
    replace_in_file(RUNITEMS_FILE, prefix, new_line,filenames)

if __name__ == "__main__":
    main()
