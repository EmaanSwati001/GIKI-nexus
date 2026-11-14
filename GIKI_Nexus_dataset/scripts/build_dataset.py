"""Build the GIKI Nexus seed dataset.

Inputs
  raw/giki_scrape_raw.json      - giki.edu.pk personnel pages + faculty listing pages (scraped)
  <coursehub>/Undergraduate-Prospectus-2025.pdf text (prosp_raw.txt) - cross-check
  <coursehub>/data/prospectus_2025/*.json, instructors_by_faculty.json - courses

Outputs (out/)
  units.json, faculty.json, other_personnel.json, research_areas.json,
  publications.json, courses.json, programs.json, build_report.json
"""
import collections, difflib, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/claude/hassan-raza-shaikh/giki_course_hub-1")
PROSP_TXT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/home/claude/prosp_raw.txt")
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
BASE = "https://giki.edu.pk"
PROSPECTUS = "GIKI Undergraduate Prospectus 2025"

raw = json.load(open(ROOT / "raw/giki_scrape_raw.json"))
SCRAPED_AT = raw["scraped_at"]

# ---------------------------------------------------------------- org units
UNITS = [
    {"id": "fcse", "name": "Faculty of Computer Science and Engineering", "short": "FCSE", "type": "faculty", "parent": None, "listing": "/fcse/faculty-profiles/"},
    {"id": "fee", "name": "Faculty of Electrical Engineering", "short": "FEE", "type": "faculty", "parent": None, "listing": "/fee/fee-faculty-profile/"},
    {"id": "fme", "name": "Faculty of Mechanical Engineering", "short": "FME", "type": "faculty", "parent": None, "listing": "/fme/fme-faculty-profile/"},
    {"id": "fbs", "name": "Faculty of Basic Sciences", "short": "FBS", "type": "faculty", "parent": None, "listing": "/fbs/es-faculty-profile/"},
    {"id": "fmce", "name": "Faculty of Materials and Chemical Engineering", "short": "FMCE", "type": "faculty", "parent": None, "listing": None},
    {"id": "dmse", "name": "Department of Materials Science and Engineering", "short": "DMSE", "type": "department", "parent": "fmce", "listing": "/fmce/dmse/dmse-faculty-profile/"},
    {"id": "dche", "name": "Department of Chemical Engineering", "short": "DChE", "type": "department", "parent": "fmce", "listing": "/fmce/dche/dche-faculty-profile/"},
    {"id": "dcve", "name": "Department of Civil Engineering", "short": "DCvE", "type": "department", "parent": None, "listing": "/dce/faculty-profile/"},
    {"id": "mgs", "name": "School of Management Sciences", "short": "MGS", "type": "faculty", "parent": None, "listing": "/mgs/mgs-faculty-profile/"},
]
for u in UNITS:
    u["source_url"] = BASE + u["listing"] if u["listing"] else None
LISTING_TO_UNIT = {u["listing"]: u["id"] for u in UNITS if u["listing"]}
COURSE_FACULTY_TO_UNIT = {"FCSE": "fcse", "FEE": "fee", "FME": "fme", "FBS": "fbs", "FMCE": "fmce", "MGS": "mgs", "Civil Engineering": "dcve"}

# ---------------------------------------------------------------- helpers
def clean(s):
    if s is None:
        return None
    s = unicodedata.normalize("NFKC", s).replace("​", "")
    s = re.sub(r"[ \t]+", " ", s).strip(" \n\t|•-–")
    return s or None

TITLE_RE = re.compile(r"\b(prof(essor)?|assoc(iate)?|asst|assistant|dr|engr|mr|ms|mrs|miss|late|dean|hod)\b\.?", re.I)
def name_key(n):
    n = re.sub(r"\(.*?\)", " ", n or "")
    n = TITLE_RE.sub(" ", n)
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode().lower()
    toks = re.findall(r"[a-z]+", n)
    return " ".join(sorted(t for t in toks if t not in {"ul", "ur", "e", "un", "al"}))

def status_from(*texts):
    t = " ".join(x for x in texts if x).lower()
    if "study leave" in t:
        return "on_study_leave"
    if "on leave" in t or "(leave" in t:
        return "on_leave"
    return "active"

def strip_status(n):
    n = re.sub(r"\((on )?(study )?leave\)|\(study leave\)|\(on leave\)", "", n or "", flags=re.I)
    n = re.sub(r"\s+((assistant|associate)\s+)?(professor|lecturer)(\s+\w+)?$|\s+dean$", "", n.strip(), flags=re.I)
    return clean(n)

# label parsing for "Qualifications: ... Research Interests: ..."
LABEL_RE = re.compile(r"(Qualifications?|Research Interests?|Research Areas?|Areas? of Interest)\s*:", re.I)
def split_labels(text):
    out = {}
    if not text:
        return out
    parts = LABEL_RE.split(text)
    # parts = [pre, label1, val1, label2, val2 ...]
    for i in range(1, len(parts) - 1, 2):
        lab = parts[i].lower()
        key = "qualifications" if lab.startswith("qualif") else "research_interests"
        val = parts[i + 1]
        if key == "research_interests":  # stop at the first blank-ish section heading after the value
            val = re.split(r"\n(?=[A-Z][A-Za-z &/()]{2,45}:?\n)", val)[0]
        val = clean(val)
        if val and key not in out:
            out[key] = val
    return out

PROSE_RE = re.compile(r"\b(holds|received|has worked|has been|focus(es|ed) on|is currently|works? on|(his|her|their) (research|work)|he is|she is)\b", re.I)
STOP_RE = re.compile(r"^(papers published|selected publications|publications|journal|conference)\b", re.I)
def interests_and_summary(raw):
    """Split a research-interest blob into (topic list, prose summary).
    Topic lists stop at the first prose sentence or a publications heading."""
    if not raw:
        return [], None
    lines = [l.strip() for l in raw.split("\n") if l.strip(" •")]
    keep = []
    for i, l in enumerate(lines):
        if STOP_RE.match(l) or re.match(r"^(e-?mail|tel|phone|ext|office|cell)\b", l, re.I):
            break
        sentences = len(re.findall(r"[a-z)]\. [A-Z]", l))
        words_per_sentence = len(l.split()) / max(sentences + 1, 1)
        long_prose = len(l) > 220 and l.count(",") < len(l) / 40
        if PROSE_RE.search(l) or long_prose or (sentences >= 2 and words_per_sentence > 16 and l.count(",") < sentences * 2):
            if i == 0 or (i == 1 and "," not in keep[0]):  # the whole field is prose (maybe under a title line)
                return [], clean(raw)
            break
        keep.append(l)
    return split_interests("\n".join(keep)), None

def split_interests(s):
    if not s:
        return []
    s = re.sub(r"\s+", " ", s.replace("•", ","))
    s = re.sub(r"(^|\s)\(?\d{1,2}[).]\s*:?\s*[-–—]?\s*", ";", s)  # numbered lists: "1): –", "2)", "3."
    s = re.sub(r"\.(\s+|$)", ";", s)  # sentence-style lists
    items = re.split(r"[;,\n]", s)
    out = []
    for it in items:
        it = re.sub(r"\S+@\S+", "", it)  # stray e-mail addresses
        it = clean(re.sub(r"^(and|&)\s+", "", it.strip(" .:"), flags=re.I))
        if it and PROSE_RE.search(it) or (it and re.match(r"^(she|he|they)\b", it, re.I)):
            continue
        if it and 2 <= len(it) <= 120 and not re.fullmatch(r"(etc|and|others?|dr|prof)", it, re.I):
            out.append(it)
    seen, res = set(), []
    for it in out:
        k = it.lower()
        if k not in seen:
            seen.add(k); res.append(it)
    return res

def split_quals(s):
    """Return (degree list, prose summary). Long narrative paragraphs go to the summary."""
    if not s:
        return [], None
    parts = re.split(r"\s*•\s*|\n|(?<=\))\s*,\s*(?=[A-Z])|;\s*", s)
    items, prose = [], []
    for p in (clean(x.strip(" ,.")) for x in parts):
        if not p or len(p) <= 2 or re.fullmatch(r"research interests?", p, re.I):
            continue
        (prose if len(p) > 160 or PROSE_RE.search(p) else items).append(p)
    return items, (" ".join(prose) or None)

# ---------------------------------------------------------------- profile sections
PUB_HEAD = re.compile(r"(publication|journal|conference|proceeding|book|chapter|patent|papers|articles)", re.I)
KNOWN_HEAD = re.compile(r"^(brief|overview|background|biography|bio|profile|about|education|qualifications?|research interests?|experience|work experience|academic experience|professional experience|teaching|courses taught|awards?|honou?rs? ?(&|and) ?awards|achievements( and awards)?|scholarships|professional (memberships|affiliations|affliations)|affiliations|memberships|research grants.*|funded projects|projects|invited talks|supervision|phd students|ms students|key responsibilities|administrative (experience|responsibilities)|skills|contact|services|editorial.*|reviewer.*|selected publications|publications.*|journal publications|conference publications|international (journal publications|conferences)|book chapters?|patents?|conference (presentations|papers|proceedings)|peer reviewed journals|research publications|academic and professional background)\s*:?$", re.I)

def is_heading(line):
    l = line.strip()
    if not l or l.startswith("•") or len(l) > 70:
        return False
    if KNOWN_HEAD.match(l):
        return True
    return l.endswith(":") and len(l) < 50 and not re.search(r"\d{4}", l)

def profile_sections(body):
    lines = [l for l in (body or "").split("\n")]
    secs, cur = collections.OrderedDict(), "_header"
    secs[cur] = []
    for l in lines:
        if is_heading(l):
            cur = clean(l.rstrip(":")) or cur
            secs.setdefault(cur, [])
        else:
            secs[cur].append(l)
    return secs

DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>,;]+)", re.I)
YEAR_RE = re.compile(r"\b(19[6-9]\d|20[0-2]\d)\b")
def pub_type(head):
    h = head.lower()
    if "patent" in h: return "patent"
    if "chapter" in h or "book" in h: return "book_or_chapter"
    if "conference" in h or "proceeding" in h or "presentation" in h: return "conference"
    if "journal" in h or "article" in h: return "journal"
    return "unspecified"

def parse_publications(secs, fid):
    pubs = []
    for head, lines in secs.items():
        if head == "_header" or not PUB_HEAD.search(head):
            continue
        merged = []
        for l in lines:
            t = clean(re.sub(r"^\s*([▪◦●○■□➢►\-*]\s*)?(\[?[A-Z]?\d{1,3}[\].)]|[A-Z]\d{1,3}\.)?\s*", "", l))
            if not t:
                continue
            # short tail fragments (venue/year/[Download]) belong to the previous entry
            if merged and (len(t) < 70 or t[0].islower()) and not re.search(r"[\u201c\"]", t):
                merged[-1] += " " + t
            else:
                merged.append(t)
        for t in merged:
            t = clean(re.sub(r"\s*\[(Download|PDF|Link)\]", "", t, flags=re.I))
            if not t or len(t) < 50:
                continue
            years = YEAR_RE.findall(t)
            doi = DOI_RE.search(t)
            pubs.append({"faculty_id": fid, "citation": t, "type": pub_type(head), "section_heading": head,
                         "year": int(years[-1]) if years else None,
                         "doi": doi.group(1).rstrip(".)") if doi else None})
    return pubs

def section_text(secs, *names):
    for h, lines in secs.items():
        if h.lower().rstrip(":") in names:
            t = clean("\n".join(lines))
            if t:
                return t
    return None

# ---------------------------------------------------------------- prospectus cross-check
def prospectus_entries():
    t = PROSP_TXT.read_text()
    entries, heading, cur = [], None, None
    for line in t.split("\n"):
        s = line.strip()
        if s.startswith("• "):
            if cur: entries.append(cur)
            cur = {"text": s[2:], "section": heading}
        elif cur and s and not s.startswith("Ghulam Ishaq") and not s.isdigit() and not s.isupper():
            if cur["text"].count("(") > cur["text"].count(")") or cur["text"].endswith(","):
                cur["text"] += " " + s
            else:
                entries.append(cur); cur = None
                heading = s if len(s) < 90 else heading
        else:
            if cur: entries.append(cur); cur = None
            if s and len(s) < 90 and not s.isdigit():
                heading = s
    if cur: entries.append(cur)
    out = []
    for e in entries:
        m = re.match(r"(.+?),\s*(.*)$", e["text"])
        if not m:
            continue
        name, rest = m.group(1), m.group(2)
        if not re.search(r"\b(Dr|Mr|Ms|Mrs|Engr|Prof)\b", name) and not re.search(r"\b(PhD|MS|BS|MSc|M\.Phil|MBA)\b", rest):
            continue
        out.append({"name": clean(name), "detail": clean(rest), "section": clean(e["section"])})
    return out

PROS = prospectus_entries()
PROS_KEYS = [(name_key(p["name"]), p) for p in PROS]
def prospectus_match(name):
    k = name_key(name)
    if not k:
        return None
    best, score = None, 0
    for pk, p in PROS_KEYS:
        r = difflib.SequenceMatcher(None, k, pk).ratio()
        if set(k.split()) == set(pk.split()):
            r = 1.0
        if r > score:
            best, score = p, r
    return (best, round(score, 2)) if score >= 0.88 else None

# ---------------------------------------------------------------- faculty
profiles = {p["url"]: p for p in raw["profiles"]}
listings = collections.defaultdict(list)
for l in raw["listings"]:
    if l["href"]:
        listings[l["href"]].append(l)

faculty, publications, report = [], [], collections.Counter()
for href, ls in listings.items():
    p = profiles.get(href, {})
    unit_ls = [l for l in ls if l["listing"] in LISTING_TO_UNIT]
    primary = unit_ls[0] if unit_ls else ls[0]
    slug = href.rstrip("/").split("/")[-1]
    fid = slug
    units = sorted({LISTING_TO_UNIT[l["listing"]] for l in unit_ls})
    lab = split_labels(primary.get("content"))
    secs = profile_sections(p.get("body"))
    plab = split_labels("\n".join(secs.get("_header", [])) + "\n" + "\n".join(
        f"{h}:\n" + "\n".join(v) for h, v in secs.items() if h != "_header" and re.match(r"(qualif|research interest)", h, re.I)))
    quals_raw = lab.get("qualifications") or plab.get("qualifications")
    ri_raw = lab.get("research_interests") or plab.get("research_interests")
    name_raw = clean(primary.get("name")) or clean(p.get("name"))
    status = status_from(primary.get("position"), name_raw, p.get("designation"))
    name = strip_status(name_raw)
    pubs = parse_publications(secs, fid)
    publications += pubs
    bio = section_text(secs, "brief", "overview", "background", "biography", "about", "profile")
    if bio is None:
        m = re.search(r"Brief:\s*(.+)", p.get("body") or "")
        bio = clean(m.group(1)) if m else None
    ri_list, ri_summary = interests_and_summary(ri_raw)
    q_items, q_summary = split_quals(quals_raw)
    pm = prospectus_match(name)
    rec = {
        "id": fid,
        "name": name,
        "designation": clean(re.sub(r"\((on )?(study )?leave\)", "", primary.get("position") or "", flags=re.I)) or clean(p.get("designation")),
        "designation_on_profile_page": clean(p.get("designation")),
        "status": status,
        "units": units,
        "email": clean((primary.get("email") or p.get("email") or "").replace(" ", "")) or None,
        "phone_or_ext": clean(primary.get("phone") or p.get("phone")),
        "office": clean(p.get("location")),
        "qualifications_raw": quals_raw,
        "qualifications": q_items,
        "qualifications_summary": q_summary,
        "research_interests_raw": ri_raw,
        "research_interests": ri_list,
        "research_summary": ri_summary,
        "bio": bio,
        "publication_count_on_profile": len(pubs),
        "profile_sections": [h for h in secs if h != "_header"],
        "photo_url": p.get("photo") if (p.get("photo") or "").startswith("http") else None,
        "profile_url": href,
        "listing_urls": sorted({BASE + l["listing"] for l in ls}),
        "website_categories": [c["slug"] for c in p.get("categories", [])],
        "prospectus_2025": ({"listed_as": pm[0]["name"], "detail": pm[0]["detail"], "section": pm[0]["section"], "match_score": pm[1]} if pm else None),
        "provenance": {"sources": [href] + sorted({BASE + l["listing"] for l in ls}) + ([PROSPECTUS] if pm else []), "scraped_at": SCRAPED_AT},
    }
    missing = [k for k in ("email",) if not rec[k]]
    if not rec["qualifications"] and not rec["qualifications_summary"]:
        missing.append("qualifications")
    if not rec["research_interests"] and not rec["research_summary"]:
        missing.append("research_interests")
    rec["missing_fields"] = missing
    # verified = identity confirmed on the official site AND key academic fields present
    rec["verified"] = bool(units) and not {"qualifications", "research_interests"} & set(missing)
    faculty.append(rec)
    report["faculty"] += 1
    for m_ in missing:
        report["missing_" + m_] += 1
    if pm: report["prospectus_matched"] += 1
    if not units: report["no_unit"] += 1

faculty.sort(key=lambda r: (r["units"][0] if r["units"] else "zzz", r["name"] or ""))

listed = set(listings)
other = []
for url, p in profiles.items():
    if url in listed:
        continue
    secs = profile_sections(p.get("body"))
    other.append({"id": p["slug"], "name": strip_status(p.get("name")), "designation": clean(p.get("designation")),
                  "email": clean(p.get("email")), "office": clean(p.get("location")),
                  "website_categories": [c["slug"] for c in p.get("categories", [])],
                  "profile_sections": [h for h in secs if h != "_header"],
                  "profile_url": url,
                  "note": "Has a personnel page on giki.edu.pk but is not on any current faculty listing page (e.g. board member, staff, former or late faculty). Not imported as current faculty.",
                  "provenance": {"sources": [url], "scraped_at": SCRAPED_AT}})

# ---------------------------------------------------------------- research areas
SYN = {"ml": "machine learning", "ai": "artificial intelligence", "dl": "deep learning", "nlp": "natural language processing",
       "iot": "internet of things", "cv": "computer vision", "llms": "large language models", "llm": "large language models",
       "large language modelling": "large language models", "internet of things (iot)": "internet of things",
       "natural language processing (nlp)": "natural language processing", "artificial intelligence (ai)": "artificial intelligence",
       "machine learning (ml)": "machine learning", "cybersecurity": "cyber security", "cyber-security": "cyber security"}
def area_key(s):
    k = re.sub(r"\s+", " ", s.lower().strip(" .")).replace("&", "and")
    k = SYN.get(k, k)
    k = re.sub(r"[^a-z0-9 ()+/-]", "", k)
    k = re.sub(r"(?<=[a-z]{4})(?<!i)(?<!u)(?<!s)(?<!ic)s$", "", k)  # fold simple plurals, keep -sis/-us/-ss/-ics
    return k.strip()

areas = {}
for f in faculty:
    keys = []
    for ri in f["research_interests"]:
        k = area_key(ri)
        if not k: continue
        a = areas.setdefault(k, {"id": re.sub(r"[^a-z0-9]+", "-", k).strip("-"), "label_variants": collections.Counter(), "faculty_ids": set(), "units": set()})
        a["label_variants"][ri] += 1; a["faculty_ids"].add(f["id"]); a["units"].update(f["units"])
        keys.append(a["id"])
    f["research_area_ids"] = sorted(set(keys))
research_areas = sorted(({"id": a["id"], "label": a["label_variants"].most_common(1)[0][0], "aliases": sorted(set(a["label_variants"]) - {a["label_variants"].most_common(1)[0][0]}),
                          "faculty_ids": sorted(a["faculty_ids"]), "faculty_count": len(a["faculty_ids"]), "units": sorted(a["units"])}
                         for a in areas.values()), key=lambda x: (-x["faculty_count"], x["id"]))

# ---------------------------------------------------------------- courses & programs
desc = json.load(open(HUB / "data/prospectus_2025/giki_course_descriptions_2025.json"))
live = json.load(open(HUB / "data/prospectus_2025/live_courses_2026-10-13.json"))
programs, offered = [], collections.defaultdict(list)
for fac in live["faculties"]:
    unit = COURSE_FACULTY_TO_UNIT.get(fac["name"])
    for prog in fac["programs"]:
        pid = re.sub(r"[^a-z0-9]+", "-", prog["name"].lower()).strip("-")
        programs.append({"id": pid, "name": prog["name"], "unit": unit, "coursehub_program_id": prog["id"]})
        for yr in prog["years"]:
            for sem in yr["semesters"]:
                for c in sem["courses"]:
                    offered[c["code"]].append({"program_id": pid, "year": c.get("year"), "semester": c.get("semester"), "name_in_catalog": c["name"]})
CODE_RE = re.compile(r"\b([A-Z]{2,4}\s?\d{3}[A-Z]?)\b")
courses = []
for code in sorted(set(desc) | set(offered)):
    d = desc.get(code, {})
    pre_raw = d.get("prereq")
    prereqs = sorted({x.replace(" ", "") for x in CODE_RE.findall(pre_raw or "")})
    name = d.get("name") or (offered[code][0]["name_in_catalog"] if offered.get(code) else None)
    courses.append({"code": code, "name": name, "credits": d.get("credits"), "prerequisites": prereqs,
                    "prerequisites_raw": None if pre_raw in (None, "None", "Nil") else pre_raw,
                    "description": d.get("description"), "unit": COURSE_FACULTY_TO_UNIT.get(d.get("faculty")),
                    "offered_in": offered.get(code, []),
                    "is_lab": code.endswith("L"),
                    "provenance": {"sources": ([f"{PROSPECTUS}, p. {d['page']}"] if d.get("page") else []) + (["GIKI Course Hub live catalog (2026-10-13)"] if offered.get(code) else [])}})

# Course Hub instructor names -> faculty ids (name match only, for later course<->instructor linking)
ibf = json.load(open(HUB / "instructors_by_faculty.json"))
fkeys = [(name_key(f["name"]), f["id"]) for f in faculty]
ch_instructors = []
for facname, names in ibf.items():
    for n in names:
        k = name_key(n); best, sc, how = None, 0, None
        for fk, fid in fkeys:
            r = 1.0 if set(k.split()) == set(fk.split()) else difflib.SequenceMatcher(None, k, fk).ratio()
            if r > sc: best, sc, how = fid, r, "full_name"
        if sc < 0.88 and k:
            toks = set(k.split())
            cands = [fid for fk, fid in fkeys if toks <= set(fk.split())]
            if len(cands) == 1:  # short form such as "Dr. Ghufran" -> unique full name
                best, sc, how = cands[0], 0.9, "unique_partial_name"
        ok = sc >= 0.88
        ch_instructors.append({"coursehub_name": n, "coursehub_faculty": facname, "faculty_id": best if ok else None,
                               "match_method": how if ok else None, "match_score": round(sc, 2)})

# ---------------------------------------------------------------- write
def dump(name, obj):
    json.dump(obj, open(OUT / name, "w"), ensure_ascii=False, indent=2)

meta = {"generated_from": ["giki.edu.pk faculty listing + personnel pages", PROSPECTUS, "GIKI Course Hub repo (giki_course_hub-1) JSON data"], "scraped_at": SCRAPED_AT}
dump("units.json", {"meta": meta, "units": UNITS})
dump("faculty.json", {"meta": meta, "count": len(faculty), "faculty": faculty})
dump("other_personnel.json", {"meta": meta, "count": len(other), "people": other})
dump("research_areas.json", {"meta": meta, "count": len(research_areas), "research_areas": research_areas})
dump("publications.json", {"meta": {**meta, "note": "Parsed from free-text publication sections on each personnel page; citation strings are verbatim, year/doi are best-effort extractions."}, "count": len(publications), "publications": publications})
dump("programs.json", {"meta": meta, "programs": programs})
dump("courses.json", {"meta": meta, "count": len(courses), "courses": courses})
dump("coursehub_instructor_links.json", {"meta": {**meta, "note": "Course Hub instructor names matched to scraped faculty by name; null faculty_id = no confident match. Who-teaches-what lives in Course Hub's course_instructors table, not in these files."}, "links": ch_instructors})

per_unit = collections.Counter(u for f in faculty for u in f["units"])
rep = {"faculty_total": len(faculty), "faculty_per_unit": dict(per_unit), "verified": sum(f["verified"] for f in faculty),
       "status": dict(collections.Counter(f["status"] for f in faculty)),
       "missing": {k: v for k, v in report.items() if k.startswith("missing_")},
       "prospectus_matched": report["prospectus_matched"], "other_personnel": len(other),
       "research_areas": len(research_areas), "publications": len(publications),
       "faculty_with_publications": sum(1 for f in faculty if f["publication_count_on_profile"]),
       "courses": len(courses), "courses_with_description": sum(1 for c in courses if c["description"]),
       "courses_in_live_catalog": sum(1 for c in courses if c["offered_in"]), "programs": len(programs),
       "coursehub_instructors": len(ch_instructors), "coursehub_instructors_matched": sum(1 for x in ch_instructors if x["faculty_id"])}
dump("build_report.json", rep)
print(json.dumps(rep, indent=1))

# ---------------------------------------------------------------- manual-review list
review = []
for f in faculty:
    why = []
    if f["missing_fields"]: why.append("missing: " + ", ".join(f["missing_fields"]))
    if len(f["qualifications"]) > 8: why.append("qualifications field looks mixed with other profile text")
    if not f["research_interests"] and f["research_summary"]: why.append("research interests only as prose (research_summary)")
    if not f["units"]: why.append("not on any department listing (found only on /faculty/)")
    if why: review.append({"id": f["id"], "name": f["name"], "units": f["units"], "reasons": why, "profile_url": f["profile_url"]})
dump("needs_review.json", {"meta": meta, "count": len(review), "records": review})
rep["needs_review"] = len(review)
dump("build_report.json", rep)
