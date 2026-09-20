#!/usr/bin/env python3
"""
One-off migration: re-encodes every book cover / series image referenced in
data.js as WebP (~100-200KB target), deletes the old file, and rewrites
data.js to point at the new .webp paths.

Usage:  python scripts/optimize_covers.py
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from image_optimize import optimize_file_to_webp

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = Path(__file__).resolve().parent.parent
DATA_JS = BASE / 'data.js'
CONVERTIBLE_EXTS = {'.jpg', '.jpeg', '.png'}


def find_cover_paths(text):
    paths = set()
    for key in ('cover', 'seriesImage'):
        paths.update(re.findall(rf'"{key}"\s*:\s*"([^"]+)"', text))
    return paths


def main():
    text = DATA_JS.read_text(encoding='utf-8')
    paths = find_cover_paths(text)

    mapping = {}
    skipped = []
    total_before = 0
    total_after = 0

    for rel_path in sorted(paths):
        src = BASE / rel_path
        ext = src.suffix.lower()
        if ext not in CONVERTIBLE_EXTS:
            if ext != '.webp':
                skipped.append((rel_path, 'unsupported/missing extension'))
            continue
        dst_rel = rel_path[:-len(src.suffix)] + '.webp'
        dst = BASE / dst_rel

        if not src.is_file():
            if dst.is_file():
                # Already converted in a previous (interrupted) run — just fix the reference.
                mapping[rel_path] = dst_rel
                print(f'{rel_path}  (already converted -> {dst_rel})')
            else:
                skipped.append((rel_path, 'file not found'))
            continue

        before = src.stat().st_size
        try:
            quality, dims, after = optimize_file_to_webp(src, dst)
        except Exception as e:
            skipped.append((rel_path, f'error: {e}'))
            continue

        src.unlink()
        mapping[rel_path] = dst_rel
        total_before += before
        total_after += after
        print(f'{rel_path}  {before/1024:.0f}KB -> {dst_rel}  {after/1024:.0f}KB (q{quality})')

    for rel_path, reason in skipped:
        print(f'SKIPPED  {rel_path}  ({reason})')

    if mapping:
        for old, new in mapping.items():
            text = text.replace(f'"{old}"', f'"{new}"')
        DATA_JS.write_text(text, encoding='utf-8')

    print()
    print(f'Converted {len(mapping)} image(s), skipped {len(skipped)}.')
    if total_before:
        print(f'Total size: {total_before/1024:.0f}KB -> {total_after/1024:.0f}KB '
              f'({100 - total_after/total_before*100:.0f}% smaller)')


if __name__ == '__main__':
    main()
