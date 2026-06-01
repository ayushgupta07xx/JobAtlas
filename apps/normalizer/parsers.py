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
        "currency": cur,
        "posted_date": _to_date(p.get("pubDate")),
        "description": desc,
        "skills": extract_skills(f"{p.get('jobTitle') or ''} {desc or ''}"),
    }


PARSERS = {"adzuna": parse_adzuna, "jobicy": parse_jobicy}
