# Legal & Ethics

JobAtlas aggregates publicly listed Indian tech job postings to make searching across portals easier. This document describes the data practices.

## Scraping principles

- Respect `robots.txt`. Skip paths a source disallows.
- Conservative rate limits: minimum one request every five seconds per source.
- Identify the crawler in a custom `User-Agent` string with a contact link.
- Cache aggressively; existing postings refresh at most once per 24 hours.
- Honor 4xx/5xx responses with exponential backoff; circuit-break on repeated 4xx.

## Data handling

- Only public, surface-level posting data is stored: title, company name, location, posted date, salary range (when published), and the canonical source URL.
- No personal data of candidates or recruiters is collected, stored, or processed.
- Postings are not redistributed; the product links users back to the original source.
- Non-commercial. Nothing is monetized, sold, or licensed.

## Takedown

If you represent a source and want postings removed from indexing, open a GitHub issue tagged `takedown` on this repo. Removals processed within 48 hours.

## APIs

Where official APIs exist (Adzuna, Jobicy), they are used in preference to scraping, within their published rate limits and ToS.
