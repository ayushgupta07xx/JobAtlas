"""Lever public postings API spider (no key, no browser).

Reads api.lever.co/v0/postings/<slug>?mode=json -- Lever's public, no-auth feed.
Returns a JSON array of postings; we keep India-relevant roles only.

    scrapy crawl lever
    scrapy crawl lever -a slug=plaid
"""

import scrapy

from jobatlas_scrapers.ats_common import LEVER, clean_text, is_india_location
from jobatlas_scrapers.items import JobItem


class LeverSpider(scrapy.Spider):
    name = "lever"
    allowed_domains = ["lever.co"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # public postings API offered for consumption
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 8,
    }
    URL = "https://api.lever.co/v0/postings/{slug}?mode=json"

    def __init__(self, slug="", *a, **k):
        super().__init__(*a, **k)
        self.slugs = {slug: LEVER.get(slug, slug)} if slug else dict(LEVER)

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
        postings = response.json()
        if not isinstance(postings, list):
            self.logger.warning("lever %s: unexpected payload shape", slug)
            return
        kept = 0
        for j in postings:
            cats = j.get("categories") or {}
            loc = cats.get("location")
            if not is_india_location(loc, j.get("workplaceType"), cats.get("allLocations")):
                continue
            j["_company"] = company
            j["_slug"] = slug
            yield JobItem(
                source="lever",
                source_job_id=j.get("id"),
                source_url=j.get("hostedUrl"),
                raw_kind="api",
                title=j.get("text"),
                company=company,
                location=loc,
                salary_text=None,
                posted_date=j.get("createdAt"),  # epoch ms; parser converts
                description=clean_text(j.get("descriptionPlain") or j.get("description")),
                skills=None,
                raw_payload=j,
            )
            kept += 1
        self.logger.info("lever %s: kept %d/%d India roles", slug, kept, len(postings))
