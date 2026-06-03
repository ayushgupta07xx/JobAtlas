"""URL canonicalization for dedup-stable source URLs.

Strips tracking/session query params (Adzuna se=/v=, utm_*, click ids) so the
same job posting maps to one canonical URL. This lets the (source, source_url)
unique constraint collapse re-fetched param-variants at ingest instead of
inserting a fresh row each time a source rotates its tracking tokens.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_DROP_PARAMS = {
    "se",
    "v",
    "ref",
    "source",
    "src",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
    "igshid",
}


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    kept = [
        (k, val)
        for k, val in parse_qsl(parts.query)
        if k.lower() not in _DROP_PARAMS and not k.lower().startswith("utm_")
    ]
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme, netloc, path, urlencode(kept), ""))
