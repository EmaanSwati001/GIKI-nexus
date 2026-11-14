import json
import re
from pathlib import Path
from collections import Counter, defaultdict

raw_dir = Path("data/raw")

def deep_audit():
    with open(raw_dir / "giki_scrape_raw.json", "r", encoding="utf-8") as f:
        scrape = json.load(f)
    with open(raw_dir / "faculty.json", "r", encoding="utf-8") as f:
        fac = json.load(f)["faculty"]
    with open(raw_dir / "courses.json", "r", encoding="utf-8") as f:
        courses = json.load(f)["courses"]
    with open(raw_dir / "publications.json", "r", encoding="utf-8") as f:
        pubs = json.load(f)["publications"]
    with open(raw_dir / "research_areas.json", "r", encoding="utf-8") as f:
        areas = json.load(f)["research_areas"]
    with open(raw_dir / "units.json", "r", encoding="utf-8") as f:
        units = json.load(f)["units"]
    with open(raw_dir / "programs.json", "r", encoding="utf-8") as f:
        progs = json.load(f)["programs"]
    with open(raw_dir / "other_personnel.json", "r", encoding="utf-8") as f:
        other = json.load(f)["people"]
    with open(raw_dir / "coursehub_instructor_links.json", "r", encoding="utf-8") as f:
        ch_links = json.load(f)["links"]
    with open(raw_dir / "needs_review.json", "r", encoding="utf-8") as f:
        review = json.load(f)["records"]

    print("=== DEEP AUDIT RESULTS ===")
    
    # 1. Scrape raw profiles and listings
    profiles = scrape["profiles"]
    listings = scrape["listings"]
    print(f"Profiles: {len(profiles)}, Listings: {len(listings)}")
    
    # Profile keys
    p_keys = Counter(k for p in profiles for k in p.keys())
    print(f"Profile keys presence: {dict(p_keys)}")
    
    # Check empty bodies in profiles
    empty_body = [p["slug"] for p in profiles if not (p.get("body") or "").strip()]
    print(f"Profiles with empty body: {len(empty_body)} -> {empty_body}")

    # Check listing keys
    l_keys = Counter(k for l in listings for k in l.keys())
    print(f"Listing keys presence: {dict(l_keys)}")

    # Check duplicate listings for same person on same page vs different pages
    person_pages = defaultdict(list)
    for l in listings:
        person_pages[l.get("href")].append(l.get("listing"))
    
    cross_listed = {k: v for k, v in person_pages.items() if len(v) > 1}
    print(f"Persons appearing in multiple listings: {len(cross_listed)}")
    for k, v in cross_listed.items():
        # check if they appear on /faculty/ plus a department page or multiple department pages
        dept_pages = [p for p in v if p != "/faculty/"]
        print(f"  {k}: total={len(v)}, pages={v}, depts={dept_pages}")

    # 2. Faculty: Conflicts in designations, names, emails
    desig_conflicts = []
    for f in fac:
        d1 = f.get("designation")
        d2 = f.get("designation_on_profile_page")
        if d1 and d2 and d1.lower() != d2.lower():
            desig_conflicts.append((f["id"], d1, d2))
    print(f"\nDesignation differences (listing vs profile page): {len(desig_conflicts)}")
    for c in desig_conflicts[:10]:
        print(f"  {c[0]}: Listing='{c[1]}' vs Profile='{c[2]}'")

    # Prospectus match scores
    pm_scores = [f["prospectus_2025"]["match_score"] for f in fac if f.get("prospectus_2025")]
    print(f"\nProspectus matches: {len(pm_scores)}, min={min(pm_scores) if pm_scores else 0}, max={max(pm_scores) if pm_scores else 0}")
    low_pm = [f for f in fac if f.get("prospectus_2025") and f["prospectus_2025"]["match_score"] < 0.95]
    print(f"Prospectus matches with score < 0.95: {len(low_pm)}")
    for f in low_pm:
        print(f"  {f['name']} -> Prospectus '{f['prospectus_2025']['listed_as']}' (score: {f['prospectus_2025']['match_score']})")

    # 3. Courses: Unit None courses
    none_unit_courses = [c for c in courses if c.get("unit") is None]
    print(f"\nCourses with unit None: {len(none_unit_courses)}")
    print(f"Sample unit None courses: {[c['code'] for c in none_unit_courses[:15]]}")
    # Check course prefixes for None unit courses
    none_prefixes = Counter(re.match(r"^[A-Za-z]+", c["code"]).group(0) if re.match(r"^[A-Za-z]+", c["code"]) else "?" for c in none_unit_courses)
    print(f"Prefixes of unit None courses: {dict(none_prefixes)}")

    # Check course descriptions and credits
    no_desc = [c["code"] for c in courses if not c.get("description")]
    print(f"Courses with no description: {len(no_desc)}")
    no_cred = [c["code"] for c in courses if c.get("credits") is None]
    print(f"Courses with no credits: {len(no_cred)}")

    # Check course prerequisites referencing non-existent courses
    all_codes = set(c["code"] for c in courses)
    broken_prereqs = defaultdict(list)
    for c in courses:
        for p in c.get("prerequisites", []):
            if p not in all_codes:
                broken_prereqs[p].append(c["code"])
    print(f"\nPrerequisites not found in courses.json: {len(broken_prereqs)} distinct missing codes")
    for p, callers in list(broken_prereqs.items())[:15]:
        print(f"  Missing prereq code '{p}' referenced by: {callers}")

    # 4. Publications: Duplicate citations across faculty or within faculty
    pub_citations = [p["citation"] for p in pubs]
    cit_counts = Counter(pub_citations)
    dups_pubs = {k: v for k, v in cit_counts.items() if v > 1}
    print(f"\nPublications total: {len(pubs)}, Unique citations: {len(cit_counts)}, Duplicates: {len(dups_pubs)}")
    
    # Co-authorship duplicate citations (same citation associated with multiple faculty_ids)
    coauthored = defaultdict(set)
    for p in pubs:
        coauthored[p["citation"]].add(p["faculty_id"])
    co_authorship_cases = {k: v for k, v in coauthored.items() if len(v) > 1}
    print(f"Co-authored publications appearing under multiple faculty: {len(co_authorship_cases)}")
    for cit, fac_set in list(co_authorship_cases.items())[:5]:
        print(f"  Faculty: {fac_set}\n    Citation: {cit[:100]}...")

    # Same faculty with identical duplicate publication
    self_dups = defaultdict(lambda: Counter())
    for p in pubs:
        self_dups[p["faculty_id"]][p["citation"]] += 1
    same_fac_dups = [(fid, cit, cnt) for fid, cnts in self_dups.items() for cit, cnt in cnts.items() if cnt > 1]
    print(f"Duplicate citations under SAME faculty member: {len(same_fac_dups)}")
    for fid, cit, cnt in same_fac_dups[:5]:
        print(f"  {fid} has {cnt} copies: {cit[:100]}...")

    # 5. CourseHub instructor links unmatched
    unmatched_ch = [l for l in ch_links if not l.get("faculty_id")]
    print(f"\nCourseHub instructors: {len(ch_links)}, Matched: {len(ch_links) - len(unmatched_ch)}, Unmatched: {len(unmatched_ch)}")
    print(f"Sample unmatched CourseHub instructors: {[l['coursehub_name'] for l in unmatched_ch[:15]]}")

    # 6. Other personnel analysis
    print(f"\nOther personnel ({len(other)}):")
    for o in other:
        print(f"  {o['id']}: {o['name']} ({o['designation']}) - categories: {o.get('website_categories')}")

if __name__ == "__main__":
    deep_audit()
