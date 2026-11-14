import json
import os
from pathlib import Path
from collections import Counter, defaultdict

def audit_all():
    raw_dir = Path("data/raw")
    files = sorted(raw_dir.glob("*.json"))
    
    print(f"Total JSON files in data/raw: {len(files)}")
    report = {}

    for f in files:
        size = f.stat().st_size
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        
        info = {
            "size_bytes": size,
            "type": type(data).__name__,
        }
        
        if isinstance(data, dict):
            info["keys"] = list(data.keys())
            for k, v in data.items():
                if isinstance(v, list):
                    info[f"list_count_{k}"] = len(v)
                elif isinstance(v, (int, str, bool, float)):
                    info[f"val_{k}"] = v
        elif isinstance(data, list):
            info["list_count"] = len(data)
            
        report[f.name] = info
        print(f"\n--- {f.name} ({size:,} bytes) ---")
        for k, v in info.items():
            print(f"  {k}: {v}")

    # Let's drill into specific files
    # 1. giki_scrape_raw.json
    print("\n================== DETAILED DRILLDOWN ==================")
    with open(raw_dir / "giki_scrape_raw.json", "r", encoding="utf-8") as fp:
        scrape_raw = json.load(fp)
    profiles = scrape_raw.get("profiles", [])
    listings = scrape_raw.get("listings", [])
    print(f"giki_scrape_raw.json: scraped_at={scrape_raw.get('scraped_at')}, profiles={len(profiles)}, listings={len(listings)}")

    # Profile URLs and uniqueness
    profile_urls = [p.get("url") for p in profiles]
    profile_slugs = [p.get("slug") for p in profiles]
    print(f"Profiles total: {len(profiles)}, unique URLs: {len(set(profile_urls))}, unique slugs: {len(set(profile_slugs))}")
    
    # Listings
    listing_urls = [l.get("href") for l in listings]
    listing_pages = Counter(l.get("listing") for l in listings)
    print(f"Listings total: {len(listings)}, unique hrefs: {len(set(listing_urls))}")
    print(f"Listings by page: {dict(listing_pages)}")
    
    # Check overlap between profiles and listings
    prof_set = set(profile_urls)
    list_set = set(listing_urls)
    print(f"In profiles but NOT in listings: {len(prof_set - list_set)}")
    print(f"In listings but NOT in profiles: {len(list_set - prof_set)}")

    # 2. faculty.json
    with open(raw_dir / "faculty.json", "r", encoding="utf-8") as fp:
        fac_data = json.load(fp)
    faculty = fac_data.get("faculty", [])
    print(f"\nfaculty.json: total records = {len(faculty)}")
    fac_ids = [f.get("id") for f in faculty]
    print(f"Unique faculty IDs: {len(set(fac_ids))}")
    fac_names = [f.get("name") for f in faculty]
    name_counts = Counter(fac_names)
    dup_names = {k: v for k, v in name_counts.items() if v > 1}
    print(f"Duplicate names in faculty.json: {dup_names}")

    # Check verified, status, units, missing_fields
    ver_count = Counter(f.get("verified") for f in faculty)
    status_count = Counter(f.get("status") for f in faculty)
    unit_dist = Counter(u for f in faculty for u in f.get("units", []))
    no_units = [f["id"] for f in faculty if not f.get("units")]
    multi_units = [f["id"] for f in faculty if len(f.get("units", [])) > 1]
    print(f"Faculty verified distribution: {dict(ver_count)}")
    print(f"Faculty status distribution: {dict(status_count)}")
    print(f"Faculty unit distribution: {dict(unit_dist)}")
    print(f"Faculty with no units: {no_units}")
    print(f"Faculty with multiple units: {multi_units}")

    # Missing fields distribution
    missing_dist = Counter()
    for f in faculty:
        for m in f.get("missing_fields", []):
            missing_dist[m] += 1
    print(f"Faculty missing fields distribution: {dict(missing_dist)}")

    # 3. courses.json
    with open(raw_dir / "courses.json", "r", encoding="utf-8") as fp:
        course_data = json.load(fp)
    courses = course_data.get("courses", [])
    print(f"\ncourses.json: total records = {len(courses)}")
    c_codes = [c.get("code") for c in courses]
    print(f"Unique course codes: {len(set(c_codes))}")
    c_units = Counter(c.get("unit") for c in courses)
    print(f"Courses per unit: {dict(c_units)}")
    no_desc = sum(1 for c in courses if not c.get("description"))
    no_credits = sum(1 for c in courses if c.get("credits") is None)
    no_name = sum(1 for c in courses if not c.get("name"))
    no_prereqs = sum(1 for c in courses if not c.get("prerequisites"))
    print(f"Courses without description: {no_desc}, without credits: {no_credits}, without name: {no_name}, without prereqs: {no_prereqs}")

    # 4. publications.json
    with open(raw_dir / "publications.json", "r", encoding="utf-8") as fp:
        pub_data = json.load(fp)
    publications = pub_data.get("publications", [])
    print(f"\npublications.json: total records = {len(publications)}")
    pub_types = Counter(p.get("type") for p in publications)
    print(f"Publication types: {dict(pub_types)}")
    pub_years = Counter(bool(p.get("year")) for p in publications)
    pub_dois = Counter(bool(p.get("doi")) for p in publications)
    print(f"Publications with year: {pub_years.get(True)}, without: {pub_years.get(False)}")
    print(f"Publications with DOI: {pub_dois.get(True)}, without: {pub_dois.get(False)}")
    pub_faculty = Counter(p.get("faculty_id") for p in publications)
    print(f"Faculty members with publications: {len(pub_faculty)}")

    # 5. research_areas.json
    with open(raw_dir / "research_areas.json", "r", encoding="utf-8") as fp:
        ra_data = json.load(fp)
    areas = ra_data.get("research_areas", [])
    print(f"\nresearch_areas.json: total records = {len(areas)}")
    area_ids = [a.get("id") for a in areas]
    print(f"Unique research area IDs: {len(set(area_ids))}")

    # 6. units.json
    with open(raw_dir / "units.json", "r", encoding="utf-8") as fp:
        u_data = json.load(fp)
    units = u_data.get("units", [])
    print(f"\nunits.json: total records = {len(units)}")
    print(f"Unit IDs: {[u.get('id') for u in units]}")

    # 7. programs.json
    with open(raw_dir / "programs.json", "r", encoding="utf-8") as fp:
        prog_data = json.load(fp)
    programs = prog_data.get("programs", [])
    print(f"\nprograms.json: total records = {len(programs)}")
    for p in programs:
        print(f"  {p.get('id')} ({p.get('name')}) - unit: {p.get('unit')}")

    # 8. other_personnel.json
    with open(raw_dir / "other_personnel.json", "r", encoding="utf-8") as fp:
        other_data = json.load(fp)
    other = other_data.get("people", [])
    print(f"\nother_personnel.json: total records = {len(other)}")

    # 9. coursehub_instructor_links.json
    with open(raw_dir / "coursehub_instructor_links.json", "r", encoding="utf-8") as fp:
        ch_data = json.load(fp)
    links = ch_data.get("links", [])
    print(f"\ncoursehub_instructor_links.json: total records = {len(links)}")
    matched_links = [l for l in links if l.get("faculty_id")]
    print(f"Matched instructor links: {len(matched_links)} / {len(links)}")

    # 10. needs_review.json
    with open(raw_dir / "needs_review.json", "r", encoding="utf-8") as fp:
        rev_data = json.load(fp)
    records = rev_data.get("records", [])
    print(f"\nneeds_review.json: total records = {len(records)}")
    reasons = Counter()
    for r in records:
        for reason in r.get("reasons", []):
            reasons[reason] += 1
    print(f"Review reasons: {dict(reasons)}")

if __name__ == "__main__":
    audit_all()
