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
    print(f"  - Faculty designation discrepancies parsed : {stats['faculty']['designation_discrepancies']}")
    print(f"  - Prospectus false-positive flags          : {stats['faculty']['prospectus_flags']}")
    print(f"  - Courses prefix-mapped to units           : {stats['courses']['prefix_mapped_units']} (Unresolved: {stats['courses']['unresolved_units']})")
    print("    Mapped by unit:")
    for uid, cnt in sorted(stats['courses']['mapped_by_unit'].items()):
        print(f"      * {uid:<8}: {cnt:>3} courses")
    print(f"  - Courses with unresolved prerequisites    : {stats['courses']['courses_with_unresolved_prereqs']} (Total refs: {stats['courses']['total_unresolved_prereq_refs']})")
    print(f"  - CourseHub instructors categorized        :")
    ch_s = stats['instructor_links']
    print(f"      * Matched      : {ch_s['matched']}")
    print(f"      * Suggested    : {ch_s['suggested']}")
    print(f"      * Needs Review : {ch_s['needs_review']}")
    print(f"      * Unmatched    : {ch_s['unmatched']}")
    print(f"  - Curation Queue items aggregated          : {summary['counts']['review_queue_items']}")
    q_stats = stats['curation_queue']
    print("    By status:")
    for status, cnt in sorted(q_stats['by_status'].items()):
        print(f"      * {status:<15}: {cnt:>3} items")
    print("    By category:")
    for cat, cnt in sorted(q_stats['by_category'].items()):
        print(f"      * {cat:<32}: {cnt:>3} items")

    print("\nCleaned datasets successfully generated in data/processed/.")
    print("=" * 60)


if __name__ == "__main__":
    main()
