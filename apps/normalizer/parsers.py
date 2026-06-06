"""Per-source payload parsers: raw API/HTML payload -> normalized field dict.

Only Adzuna and Jobicy are implemented (the sources currently in the raw zone).
Wellfound/Naukri land 0 rows today; their parsers are authored against a real
raw doc when one exists. Day-5 scope = normalize Adzuna + Jobicy (per handoff).
"""

from __future__ import annotations

import html
import re
from datetime import date, datetime

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Curated tech-skill keywords for a deterministic best-effort skill tag.
_SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "golang",
    "rust",
    "c++",
    "sql",
    "scala",
    "r",
    "bash",
    "react",
    "next.js",
    "node.js",
    "django",
    "fastapi",
    "flask",
    "spring",
    "airflow",
    "dbt",
    "kafka",
    "spark",
    "hadoop",
    "snowflake",
    "bigquery",
    "redshift",
    "postgres",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "terraform",
    "aws",
    "gcp",
    "azure",
    "tableau",
    "power bi",
    "looker",
    "pandas",
    "numpy",
    "pytorch",
    "tensorflow",
    "scikit-learn",
    "nlp",
    "etl",
    "elt",
    "ci/cd",
    "git",
    "ruby",
    "rails",
]
_SKILL_PATTERNS = [
    (s, re.compile(rf"(?<![\w.+#]){re.escape(s)}(?![\w.+#])", re.I)) for s in _SKILLS
]


def strip_html(value: str | None) -> str | None:
    if not value:
        return None
    text = html.unescape(_TAG_RE.sub(" ", value))
    text = _WS_RE.sub(" ", text).strip()
    return text or None


def extract_skills(text: str | None) -> list[str] | None:
    if not text:
        return None
    found = [name for name, pat in _SKILL_PATTERNS if pat.search(text)]
    return sorted(set(found)) or None


def _to_date(value: object) -> date | None:
    if not value:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).date()
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(str(value).strip()[:19], fmt).date()
            except ValueError:
                continue
    return None


def _num(value: object) -> float | None:
    try:
        return float(value) if value not in (None, "") else None  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


# Salary text parsing for HTML sources (lakhs / k / ranges).
# API sources carry numeric salary fields, so this is unused today; it exists
# for Wellfound/Naukri HTML salary strings when they land.
_NUMTOK = re.compile(r"(\d+(?:[.,]\d+)?)\s*(lpa|lakh|lac|l|cr|crore|k)?", re.I)


def parse_salary_text(value: str | None) -> tuple[float | None, float | None]:
    if not value:
        return None, None
    mult = {
        "l": 1e5,
        "lpa": 1e5,
        "lakh": 1e5,
        "lac": 1e5,
        "cr": 1e7,
        "crore": 1e7,
        "k": 1e3,
    }
    nums: list[float] = []
    for m in _NUMTOK.finditer(value.lower()):
        n = float(m.group(1).replace(",", ""))
        nums.append(n * mult.get(m.group(2) or "", 1.0))
    if not nums:
        return None, None
    return (min(nums), max(nums)) if len(nums) > 1 else (nums[0], nums[0])


# --- salary from free-text descriptions ------------------------------------
# High-precision INR pay-range extractor for sources whose structured salary is
# null (Adzuna recruiters often paste a range into the body). Anchors on a pay
# cue, requires a ₹/INR symbol or a lakh/cr unit, ANNUALIZES "per month" figures,
# handles ranges where only one bound carries the symbol, and bounds the result
# -- so the §17 dashboards and salary regression never ingest a bad figure.
_PAY_CUE = re.compile(
    r"(pay range|salary|compensation|remuneration|\bctc\b|per annum|stipend)", re.I
)
_MONTHLY = re.compile(r"per month|/\s*month|\bmonthly\b", re.I)
_CUR = r"(?:₹|rs\.?|inr)"
_UNIT = r"(lpa|lakhs?|lacs?|crores?|cr|k)"
_NUM = r"\d+(?:[,.]\d+)*"
# range: A [to|-|–|—] B, currency optional on each, unit optional + shared
_RANGE = re.compile(rf"{_CUR}?\s*({_NUM})\s*(?:to|[-–—])\s*{_CUR}?\s*({_NUM})\s*{_UNIT}?", re.I)
# single amount: requires a currency prefix OR a trailing unit
_SINGLE = re.compile(rf"(?:{_CUR}\s*({_NUM})\s*{_UNIT}?)|(?:({_NUM})\s*{_UNIT})", re.I)
_UNIT_MULT = {
    "lpa": 1e5,
    "lakh": 1e5,
    "lakhs": 1e5,
    "lac": 1e5,
    "lacs": 1e5,
    "cr": 1e7,
    "crore": 1e7,
    "crores": 1e7,
    "k": 1e3,
}
_SAL_LO, _SAL_HI = 50_000.0, 100_000_000.0


def _to_inr(num: str, unit: str | None) -> float:
    return float(num.replace(",", "")) * _UNIT_MULT.get((unit or "").lower(), 1.0)


def salary_from_description(desc: str | None) -> tuple[float | None, float | None]:
    """Best-effort annual-INR pay range from a description; (None, None) if absent."""
    if not desc:
        return None, None
    cue = _PAY_CUE.search(desc)
    if not cue:
        return None, None
    window = desc[cue.start() : cue.start() + 200]
    factor = 12.0 if _MONTHLY.search(window) else 1.0
    vals: list[float] = []
    for m in _RANGE.finditer(window):
        blob = m.group(0).lower()
        if not (m.group(3) or "₹" in blob or "rs" in blob or "inr" in blob):
            continue  # bare-number range (headcount, etc.) -- skip
        vals += [_to_inr(m.group(1), m.group(3)), _to_inr(m.group(2), m.group(3))]
    if not vals:  # no range matched; fall back to single tagged amounts
        for m in _SINGLE.finditer(window):
            num = m.group(1) or m.group(3)
            if num:
                vals.append(_to_inr(num, m.group(2) or m.group(4)))
    vals = [v * factor for v in vals if _SAL_LO <= v * factor <= _SAL_HI]
    if not vals:
        return None, None
    return (min(vals), max(vals)) if len(vals) > 1 else (vals[0], vals[0])


# --- experience from free-text descriptions --------------------------------
# Best-effort required-experience range (years) from a description. No source
# (Adzuna included) exposes a structured experience field, so it is regex-read
# from the body, with the year figure required ADJACENT to the word "experience"
# (<=25 chars, no sentence break) to suppress noun-phrase hits like "customer
# experience" or "Experience Design". Bounded 0-40 yrs; (None, None) if absent.
# Powers the salary-by-city/role/experience dashboard dimension; unmatched rows
# surface as an explicit "Not specified" band.
_EXP_BEFORE = re.compile(
    r"(\d{1,2})\s*(?:\+|\s*(?:-|to|–|—)\s*(\d{1,2}))?\s*\+?\s*"
    r"(?:years?|yrs?)[^.]{0,25}?experience",
    re.I,
)
_EXP_AFTER = re.compile(
    r"experience[^.]{0,25}?(\d{1,2})\s*(?:\+|\s*(?:-|to|–|—)\s*(\d{1,2}))?\s*\+?\s*"
    r"(?:years?|yrs?)",
    re.I,
)
_EXP_LO, _EXP_HI = 0, 40


def experience_from_description(desc: str | None) -> tuple[int | None, int | None]:
    """Best-effort (min_years, max_years) of required experience; (None, None) if absent."""
    if not desc:
        return None, None
    mins: list[int] = []
    maxes: list[int] = []
    for rx in (_EXP_BEFORE, _EXP_AFTER):
        for m in rx.finditer(desc):
            lo = int(m.group(1))
            hi = int(m.group(2)) if m.group(2) else lo
            if hi < lo:
                lo, hi = hi, lo
            if _EXP_LO <= lo <= _EXP_HI and _EXP_LO <= hi <= _EXP_HI:
                mins.append(lo)
                maxes.append(hi)
    if not mins:
        return None, None
    return min(mins), max(maxes)


# jobGeo -> ISO-3166 alpha-2 (best-effort; "ZZ" = unknown/worldwide).
_GEO = {
    "usa": "US",
    "united states": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "india": "IN",
    "canada": "CA",
    "germany": "DE",
    "france": "FR",
    "australia": "AU",
    "spain": "ES",
    "netherlands": "NL",
    "ireland": "IE",
    "poland": "PL",
    "brazil": "BR",
    "singapore": "SG",
    "emea": "ZZ",
    "anywhere": "ZZ",
    "worldwide": "ZZ",
    "remote": "ZZ",
}


def _geo_to_country(value: str | None) -> str:
    return _GEO.get((value or "").strip().lower(), "ZZ")


def parse_adzuna(p: dict) -> dict:
    area = (p.get("location") or {}).get("area") or []
    state = area[1] if len(area) >= 3 else None
    city = area[-1] if len(area) >= 2 else None
    desc = p.get("description")
    return {
        "title": p.get("title"),
        "company": (p.get("company") or {}).get("display_name"),
        "city": city,
        "state": state,
        "country": "IN",  # Adzuna India endpoint
        "salary_min": _num(p.get("salary_min")),
        "salary_max": _num(p.get("salary_max")),
        "currency": "INR",  # adzuna.in salaries are INR
        "posted_date": _to_date(p.get("created")),
        "description": desc,
        "skills": extract_skills(f"{p.get('title') or ''} {desc or ''}"),
    }


def parse_jobicy(p: dict) -> dict:
    desc = strip_html(p.get("jobDescription"))
    cur = (p.get("salaryCurrency") or "USD").upper()[:3]
    return {
        "title": p.get("jobTitle"),
        "company": p.get("companyName"),
        "city": None,  # Jobicy is remote-first; no city granularity
        "state": None,
        "country": _geo_to_country(p.get("jobGeo")),
        "salary_min": _num(p.get("annualSalaryMin")),
        "salary_max": _num(p.get("annualSalaryMax")),
        "currency": cur or "INR",
        "posted_date": _to_date(p.get("pubDate")),
        "description": desc,
        "skills": extract_skills(f"{p.get('jobTitle') or ''} {desc or ''}"),
    }


PARSERS = {"adzuna": parse_adzuna, "jobicy": parse_jobicy}


# --- ATS feeds (Greenhouse / Lever / Ashby) --------------------------------
# Each takes the verbatim board payload landed by its spider and maps it to the
# normalized staging.jobs field dict. Defensive .get() throughout: a shape drift
# yields nulls (caught by the GX gate) rather than crashing the normalizer.

_IN_CITIES = (
    "bengaluru",
    "bangalore",
    "mumbai",
    "pune",
    "hyderabad",
    "delhi",
    "gurgaon",
    "gurugram",
    "noida",
    "chennai",
    "kolkata",
    "ahmedabad",
)


def _india_country(*parts: object) -> str:
    blob = " ".join(str(p) for p in parts if p).lower()
    if "india" in blob or any(c in blob for c in _IN_CITIES):
        return "IN"
    return "ZZ"  # India-eligible remote that passed the spider filter


def _split_city_state(loc: object) -> tuple[str | None, str | None]:
    if not loc:
        return None, None
    bits = [p.strip() for p in str(loc).split(",") if p.strip()]
    if not bits:
        return None, None
    city = bits[0]
    state = bits[1] if len(bits) >= 2 and bits[1].lower() != "india" else None
    return city, state


def parse_greenhouse(p: dict) -> dict:
    loc = (p.get("location") or {}).get("name")
    city, state = _split_city_state(loc)
    desc = strip_html(p.get("content"))
    title = p.get("title")
    offices = " ".join(o.get("location") or "" for o in (p.get("offices") or []))
    return {
        "title": title,
        "company": p.get("_company"),
        "city": city,
        "state": state,
        "country": _india_country(loc, offices),
        "salary_min": None,
        "salary_max": None,
        "currency": "INR",
        "posted_date": _to_date(p.get("updated_at")),
        "description": desc,
        "skills": extract_skills(f"{title or ''} {desc or ''}"),
    }


def parse_lever(p: dict) -> dict:
    cats = p.get("categories") or {}
    loc = cats.get("location")
    city, state = _split_city_state(loc)
    desc = strip_html(p.get("description")) or p.get("descriptionPlain")
    title = p.get("text")
    sr = p.get("salaryRange") or {}
    created = p.get("createdAt")
    posted = (
        datetime.fromtimestamp(created / 1000).date()
        if isinstance(created, (int, float))
        else _to_date(created)
    )
    cur = (sr.get("currency") or "").upper()[:3] or None
    return {
        "title": title,
        "company": p.get("_company"),
        "city": city,
        "state": state,
        "country": _india_country(loc, cats.get("allLocations")),
        "salary_min": _num(sr.get("min")),
        "salary_max": _num(sr.get("max")),
        "currency": cur or "INR",
        "posted_date": posted,
        "description": desc,
        "skills": extract_skills(f"{title or ''} {desc or ''}"),
    }


def parse_ashby(p: dict) -> dict:
    loc = p.get("location")
    city, state = _split_city_state(loc)
    desc = p.get("descriptionPlain") or strip_html(p.get("descriptionHtml"))
    title = p.get("title")
    tiers = (p.get("compensation") or {}).get("compensationTiers") or []
    smin = smax = cur = None
    if tiers:
        t0 = tiers[0] or {}
        smin, smax = _num(t0.get("minValue")), _num(t0.get("maxValue"))
        cur = (t0.get("currency") or "").upper()[:3] or None
    addr = ((p.get("address") or {}).get("postalAddress")) or {}
    return {
        "title": title,
        "company": p.get("_company"),
        "city": city,
        "state": state,
        "country": _india_country(loc, addr.get("addressCountry"), addr.get("addressLocality")),
        "salary_min": smin,
        "salary_max": smax,
        "currency": cur or "INR",
        "posted_date": _to_date(p.get("publishedAt")),
        "description": desc,
        "skills": extract_skills(f"{title or ''} {desc or ''}"),
    }


PARSERS = {
    **PARSERS,
    "greenhouse": parse_greenhouse,
    "lever": parse_lever,
    "ashby": parse_ashby,
}


# --- remote feeds (RemoteOK / Remotive) ------------------------------------
# Remote-first aggregators; we keep India-eligible roles only (filtered in the
# spiders). country = IN when the location names India, else ZZ (worldwide).


def parse_remoteok(p: dict) -> dict:
    loc = p.get("location") or "Worldwide"
    title = p.get("position") or p.get("title")
    desc = strip_html(p.get("description"))
    tags = " ".join(p.get("tags") or [])
    return {
        "title": title,
        "company": p.get("company"),
        "city": None,
        "state": None,
        "country": _india_country(loc),
        "salary_min": _num(p.get("salary_min")),
        "salary_max": _num(p.get("salary_max")),
        "currency": "USD",
        "posted_date": _to_date(p.get("date")),
        "description": desc,
        "skills": extract_skills(f"{title or ''} {tags} {desc or ''}"),
    }


def parse_remotive(p: dict) -> dict:
    crl = p.get("candidate_required_location") or "Worldwide"
    title = p.get("title")
    desc = strip_html(p.get("description"))
    tags = " ".join(p.get("tags") or [])
    country = _india_country(crl)
    return {
        "title": title,
        "company": p.get("company_name"),
        "city": None,
        "state": None,
        "country": country,
        "salary_min": None,
        "salary_max": None,
        "currency": "INR" if country == "IN" else "USD",
        "posted_date": _to_date(p.get("publication_date")),
        "description": desc,
        "skills": extract_skills(f"{title or ''} {tags} {desc or ''}"),
    }


PARSERS = {**PARSERS, "remoteok": parse_remoteok, "remotive": parse_remotive}


# --- The Muse (public API) -------------------------------------------------
# Tech-category roles in India hubs; the spider already drops non-India rows.
# The Muse exposes no salary, so currency defaults to INR (column is NOT NULL).


def parse_themuse(p: dict) -> dict:
    locs = [loc.get("name") for loc in (p.get("locations") or []) if loc.get("name")]
    primary = locs[0] if locs else ""
    city, state = _split_city_state(primary)
    if state and state.strip().lower() == "india":
        state = None
    title = p.get("name")
    desc = strip_html(p.get("contents"))
    cats = " ".join(c.get("name", "") for c in (p.get("categories") or []))
    return {
        "title": title,
        "company": (p.get("company") or {}).get("name"),
        "city": city,
        "state": state,
        "country": _india_country(primary),
        "salary_min": None,
        "salary_max": None,
        "currency": "INR",
        "posted_date": _to_date(p.get("publication_date")),
        "description": desc,
        "skills": extract_skills(f"{title or ''} {cats} {desc or ''}"),
    }


PARSERS = {**PARSERS, "themuse": parse_themuse}
