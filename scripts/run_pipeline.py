"""
Run the full GIKI Nexus data cleaning and processing pipeline.
Reads from data/raw/, validates, cleans, deduplicates, and saves to data/processed/.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.data_processing.pipeline import DataPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    raw_dir = PROJECT_ROOT / "data" / "raw"
    processed_dir = PROJECT_ROOT / "data" / "processed"

    print("=" * 60)
    print("GIKI NEXUS - DATA PROCESSING PIPELINE")
    print("=" * 60)
    print(f"Source Directory   : {raw_dir}")
    print(f"Destination Output : {processed_dir}")

    # Track raw files last modified timestamp to ensure raw files are untouched
    raw_files = list(raw_dir.glob("*.json"))
    initial_mtimes = {f.name: f.stat().st_mtime for f in raw_files}

    pipeline = DataPipeline(raw_dir=raw_dir, processed_dir=processed_dir)
    summary = pipeline.run()

    # Verify raw files were not touched
    raw_untouched = True
    for f in raw_files:
        if f.stat().st_mtime != initial_mtimes[f.name]:
            raw_untouched = False
            print(f"WARNING: Raw file {f.name} was modified!")

    if raw_untouched:
        print("[SUCCESS] Verified: Original raw files remain completely untouched.")

    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Processed Entities:")
    for entity, count in summary["counts"].items():
        print(f"  - {entity.replace('_', ' ').title():<28}: {count:,} records")

    print("\nCleaning & Deduplication Highlights:")
    stats = summary["statistics"]
    print(f"  - Publications duplicate citations removed : {stats['publications']['duplicates_removed']}")
    print(f"  - Research Areas ID collisions resolved    : {stats['research_areas']['id_collisions_resolved']}")
    print(f"  - Faculty verified                         : {stats['faculty']['verified']} / {summary['counts']['faculty']}")
    print(f"  - Prospectus false-positive flags          : {stats['faculty']['prospectus_flags']}")
    print(f"  - Review Queue items aggregated            : {summary['counts']['review_queue_items']}")

    print("\nCleaned datasets successfully generated in data/processed/.")
    print("=" * 60)


if __name__ == "__main__":
    main()
