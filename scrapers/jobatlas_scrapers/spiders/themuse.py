"""The Muse public jobs API spider (authorized public API, no browser).

Free tier: 500 requests/hour unregistered (set THEMUSE_API_KEY for 3600/hr).
We fan out tech categories x India hubs. The Muse location filter is soft, so
we keep only India / India-eligible rows via the shared is_india_location().
Yields JobItem; landing handled by RawLandingPipeline.
"""

import os
from urllib.parse import urlencode

import scrapy
from dotenv import find_dotenv, load_dotenv

from jobatlas_scrapers.ats_common import clean_text, is_india_location
from jobatlas_scrapers.items import JobItem

TECH_CATEGORIES = [
    "Software Engineering",
    "Data Science",
    "Data and Analytics",
    "IT",
    "Engineering",
    "Product Management",
]

INDIA_LOCATIONS = [
    "Bangalore, India",
    "Mumbai, India",
    "New Delhi, India",
    "Hyderabad, India",
    "Pune, India",
    "Chennai, India",
    "Gurgaon, India",
    "Noida, India",
    "Kolkata, India",
    "Ahmedabad, India",
]


def _loc_names(r: dict) -> list[str]:
    return [loc.get("name") for loc in (r.get("locations") or []) if loc.get("name")]


class TheMuseSpider(scrapy.Spider):
    name = "themuse"
    allowed_domains = ["themuse.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 1.0,
    }

    BASE = "https://www.themuse.com/api/public/jobs"

    def __init__(self, max_pages=15, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages)
        self._kept = 0
        self._seen = 0
        load_dotenv(find_dotenv())
        self.api_key = os.environ.get("THEMUSE_API_KEY")

    async def start(self):
        for category in TECH_CATEGORIES:
            for location in INDIA_LOCATIONS:
                yield self._page_request(1, category, location)

    def _page_request(self, page, category, location):
        params = {"category": category, "location": location, "page": page}
        if self.api_key:
            params["api_key"] = self.api_key
        url = self.BASE + "?" + urlencode(params)
        return scrapy.Request(
            url,
            callback=self.parse,
            cb_kwargs={"page": page, "category": category, "location": location},
        )

    def parse(self, response, page, category, location):
        data = response.json()
        results = data.get("results", [])
        for r in results:
            self._seen += 1
            if not any(is_india_location(x) for x in _loc_names(r)):
                continue
            self._kept += 1
            yield self._to_item(r)
        page_count = data.get("page_count", 0)
        if results and page < self.max_pages and page < page_count:
            yield self._page_request(page + 1, category, location)

    def closed(self, reason):
        self.logger.info("themuse: kept %d/%d India-eligible roles", self._kept, self._seen)

    def _to_item(self, r):
        locs = _loc_names(r)
        india_loc = next(
            (x for x in locs if is_india_location(x)),
            locs[0] if locs else None,
        )
        return JobItem(
            source="themuse",
            source_job_id=str(r["id"]) if r.get("id") is not None else None,
            source_url=(r.get("refs") or {}).get("landing_page"),
            raw_kind="api",
            title=r.get("name"),
            company=(r.get("company") or {}).get("name"),
            location=india_loc,
            salary_text=None,
            posted_date=r.get("publication_date"),
            description=clean_text(r.get("contents")),
            skills=None,
            raw_payload=r,
        )
