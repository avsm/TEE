#!/usr/bin/env python3
"""
Migrate existing JSON labels to SQLite database.

Usage:
    python3 migrate_labels_to_sqlite.py

This will:
1. Find all *_labels.json files in viewports/
2. Import each label and its pixels into SQLite
3. Report migration statistics

The original JSON files are NOT deleted (kept as backup).
"""

import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from backend.labels_db import init_db, save_label, get_label_count, DB_PATH


def migrate():
    """Migrate all JSON labels to SQLite."""
    print("=" * 60)
    print("Labels Migration: JSON -> SQLite")
    print("=" * 60)

    # Initialize database
    init_db()
    print(f"\nDatabase: {DB_PATH}")

    viewports_dir = Path(__file__).parent / 'viewports'
    json_files = list(viewports_dir.glob('*_labels.json'))

    if not json_files:
        print("\nNo JSON label files found. Nothing to migrate.")
        return

    print(f"\nFound {len(json_files)} label files to migrate:\n")

    total_labels = 0
    total_pixels = 0
    errors = []

    for json_file in sorted(json_files):
        viewport_name = json_file.stem.replace('_labels', '')

        # Check if already migrated
        existing_count = get_label_count(viewport_name)
        if existing_count > 0:
            print(f"  {viewport_name}: SKIPPED ({existing_count} labels already in DB)")
            continue

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            labels = data.get('labels', [])
            viewport_pixels = 0

            for label in labels:
                try:
                    save_label(viewport_name, label)
                    total_labels += 1
                    viewport_pixels += len(label.get('pixels', []))
                except Exception as e:
                    errors.append(f"{viewport_name}/{label.get('name', 'unknown')}: {e}")

            total_pixels += viewport_pixels
            file_size_mb = json_file.stat().st_size / (1024 * 1024)
            print(f"  {viewport_name}: {len(labels)} labels, {viewport_pixels:,} pixels ({file_size_mb:.1f} MB JSON)")

        except Exception as e:
            errors.append(f"{viewport_name}: {e}")
            print(f"  {viewport_name}: ERROR - {e}")

    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"  Labels migrated: {total_labels}")
    print(f"  Pixels migrated: {total_pixels:,}")
    print(f"  Database size:   {DB_PATH.stat().st_size / (1024 * 1024):.1f} MB")

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for error in errors:
            print(f"    - {error}")

    print("\nOriginal JSON files have been preserved as backup.")
    print("Once verified, you can delete them manually if desired.")


if __name__ == '__main__':
    migrate()
