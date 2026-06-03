"""Ashby public job-board API spider (no key, no browser).

Reads api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true --
Ashby's public, no-auth feed (the cleanest of the three for salary data).
Returns {"jobs": [...]}; we keep India-relevant roles only.

    scrapy crawl ashby
    scrapy crawl ashby -a slug=linear
"""

import scrapy

from jobatlas_scrapers.ats_common import ASHBY, clean_text, is_india_location
from jobatlas_scrapers.items import JobItem


class AshbySpider(scrapy.Spider):
    name = "ashby"
    allowed_domains = ["ashbyhq.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # public job-board API offered for consumption
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 8,
    }
    URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"

    def __init__(self, slug="", *a, **k):
        super().__init__(*a, **k)
        self.slugs = {slug: ASHBY.get(slug, slug)} if slug else dict(ASHBY)

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
            sec = " ".join(s.get("location") or "" for s in (j.get("secondaryLocations") or []))
            addr = ((j.get("address") or {}).get("postalAddress")) or {}
            if not is_india_location(j.get("location"), sec, addr.get("addressCountry")):
                continue
            j["_company"] = company
            j["_slug"] = slug
            yield JobItem(
                source="ashby",
                source_job_id=j.get("id"),
                source_url=j.get("jobUrl"),
                raw_kind="api",
                title=j.get("title"),
                company=company,
                location=j.get("location"),
                salary_text=None,
                posted_date=j.get("publishedAt"),
                description=clean_text(j.get("descriptionPlain") or j.get("descriptionHtml")),
                skills=None,
                raw_payload=j,
            )
            kept += 1
        self.logger.info("ashby %s: kept %d/%d India roles", slug, kept, len(jobs))
