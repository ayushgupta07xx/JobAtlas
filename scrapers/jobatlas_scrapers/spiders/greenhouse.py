"""Greenhouse public job-board API spider (no key, no browser).

Reads boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true -- the public
endpoint a company's own careers page calls. One request per board returns every
open role; we keep India-relevant roles only. No login/proxy/anti-bot bypass.

    scrapy crawl greenhouse                 # full seed list
    scrapy crawl greenhouse -a slug=stripe  # single board, for a smoke test
"""

import scrapy

from jobatlas_scrapers.ats_common import GREENHOUSE, clean_text, is_india_location
from jobatlas_scrapers.items import JobItem


class GreenhouseSpider(scrapy.Spider):
    name = "greenhouse"
    allowed_domains = ["greenhouse.io"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # public board API offered for consumption
        "DOWNLOAD_DELAY": 0.5,  # polite; one request per board
        "CONCURRENT_REQUESTS": 8,
    }
    URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

    def __init__(self, slug="", *a, **k):
        super().__init__(*a, **k)
        self.slugs = {slug: GREENHOUSE.get(slug, slug)} if slug else dict(GREENHOUSE)

    async def start(self):
        for slug in self.slugs:
            yield scrapy.Request(
                self.URL.format(slug=slug),
                callback=self.parse,
                cb_kwargs={"slug": slug},
                dont_filter=True,
            )

    def parse(self, response, slug):
        company = self.slugs.get(slug, slug)
        jobs = response.json().get("jobs", [])
        kept = 0
        for j in jobs:
            loc = (j.get("location") or {}).get("name")
            offices = " ".join(o.get("location") or "" for o in (j.get("offices") or []))
            if not is_india_location(loc, offices):
                continue
            j["_company"] = company  # Greenhouse jobs carry no company name
            j["_slug"] = slug
            yield JobItem(
                source="greenhouse",
                source_job_id=str(j.get("id")) if j.get("id") is not None else None,
                source_url=j.get("absolute_url"),
                raw_kind="api",
                title=j.get("title"),
                company=company,
                location=loc,
                salary_text=None,  # Greenhouse public board carries no salary
                posted_date=j.get("updated_at"),
                description=clean_text(j.get("content")),  # full HTML kept in raw_payload
                skills=None,
                raw_payload=j,
            )
            kept += 1
        self.logger.info("greenhouse %s: kept %d/%d India roles", slug, kept, len(jobs))
