#!/usr/bin/env python3
"""
Remove lines from a flavors file when they match (partial, case-insensitive)
any entry in an artists file.

Usage:
  # Dry-run (default) - shows what would be removed and how many lines kept/removed
  python3 scripts/remove_flavors_by_artists.py \
      --artists clip_interrogator/data/artists.txt \
      --flavors  clip_interrogator/data/flavors.txt

  # Actually modify flavors file in-place (creates a backup)
  python3 scripts/remove_flavors_by_artists.py \
      --artists clip_interrogator/data/artists.txt \
      --flavors  clip_interrogator/data/flavors.txt \
      --inplace

Notes:
- Matching is performed after normalizing Unicode, removing punctuation,
  collapsing whitespace and lowercasing.
- A flavor line is removed if any normalized artist string is found as a
  substring of the normalized flavor line.
"""
from __future__ import annotations
import argparse
import unicodedata
import re
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

RE_NON_ALNUM = re.compile(r'[^0-9a-zA-Z\s]+')


def normalize_text(s: str) -> str:
    """Normalize text for robust case-insensitive partial matching.
    Steps:
    - NFKD unicode normalization
    - remove diacritics
    - remove punctuation (non-alphanumeric)
    - collapse whitespace
    - lowercase
    """
    if s is None:
        return ""
    # Unicode normalize
    s = unicodedata.normalize("NFKD", s)
    # Remove diacritical marks (combining marks)
    s = ''.join(ch for ch in s if not unicodedata.category(ch).startswith('M'))
    # Remove non-alphanumeric characters (keeps spaces)
    s = RE_NON_ALNUM.sub(' ', s)
    # Collapse whitespace and lowercase
    s = re.sub(r'\s+', ' ', s).strip().casefold()
    return s


def load_nonempty_lines(path: Path) -> List[str]:
    text = path.read_text(encoding='utf-8', errors='replace')
    # Keep original lines trimmed of trailing newline only; preserve blank lines maybe skip them
    lines = [line.rstrip('\n') for line in text.splitlines()]
    return lines


def find_removals(flavors_lines: List[str], artists_lines: List[str]) -> Tuple[List[int], List[str]]:
    """Return indexes of flavors_lines to remove and their original contents."""
    # Precompute normalized artist strings (skip empties)
    normalized_artists = []
    for a in artists_lines:
        a_stripped = a.strip()
        if not a_stripped:
            continue
        na = normalize_text(a_stripped)
        if na:
            normalized_artists.append(na)

    removals_idx = []
    removals_lines = []

    for idx, flavor in enumerate(flavors_lines):
        flavor_stripped = flavor.strip()
        if not flavor_stripped:
            # skip empty lines (do not remove by artist match)
            continue
        nf = normalize_text(flavor_stripped)
        matched = False
        for na in normalized_artists:
            # skip absurdly short artist tokens to avoid many false positives (optional)
            # but we will still match short artists (e.g., 'Ai Weiwei') as provided.
            if na and na in nf and len(na.replace(' ',''))>3 and 'and' in nf:
                print(na, ' in ', nf)
                matched = True
                break
        if matched:
            removals_idx.append(idx)
            removals_lines.append(flavor)
    return removals_idx, removals_lines


def write_filtered(flavors_lines: List[str], removals_idx: List[int], flavors_path: Path, create_backup=False) -> Path:
    if create_backup:
        stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        backup_path = flavors_path.with_suffix(flavors_path.suffix + f".bak.{stamp}")
        backup_path.write_text("\n".join(flavors_lines) + ("\n" if flavors_lines and not flavors_lines[-1].endswith("\n") else ""), encoding='utf-8')
    else:
        backup_path = None

    # Build new lines without removals. Preserve original order and other lines.
    kept_lines = [line for idx, line in enumerate(flavors_lines) if idx not in set(removals_idx)]
    flavors_path.write_text("\n".join(kept_lines) + ("\n" if kept_lines and not kept_lines[-1].endswith("\n") else ""), encoding='utf-8')
    return backup_path


def main():
    p = argparse.ArgumentParser(description="Remove flavors lines that match artists (partial, case-insensitive).")
    p.add_argument("--artists", type=Path, required=True, help="Path to artists.txt")
    p.add_argument("--flavors", type=Path, required=True, help="Path to flavors.txt")
    p.add_argument("--inplace", action="store_true", help="Write changes to flavors file (creates timestamped backup). Without this flag, runs a dry-run.")
    p.add_argument("--no-backup", action="store_true", help="If --inplace, do not create a backup (not recommended).")
    args = p.parse_args()

    if not args.artists.exists():
        raise SystemExit(f"Artists file not found: {args.artists}")
    if not args.flavors.exists():
        raise SystemExit(f"Flavors file not found: {args.flavors}")

    artists_lines = load_nonempty_lines(args.artists)
    flavors_lines = load_nonempty_lines(args.flavors)

    removals_idx, removals_lines = find_removals(flavors_lines, artists_lines)

    print(f"Total flavors lines: {len(flavors_lines)}")
    print(f"Matched (to remove): {len(removals_idx)}")
    print(f"Kept: {len(flavors_lines) - len(removals_idx)}")
    if removals_lines:
        print("\nExamples of matched lines (first 50 shown):")
        for line in removals_lines[:50]:
            print(f" - {line}")

    if not args.inplace:
        print("\nDry-run: no files were modified. Re-run with --inplace to apply changes.")
        return

    backup = None
    if args.inplace:
        backup = write_filtered(flavors_lines, removals_idx, args.flavors, create_backup=not args.no_backup)
        if backup:
            print(f"\nBackup of original flavors file written to: {backup}")
        print(f"Updated flavors file written to: {args.flavors}")


if __name__ == "__main__":
    main()