"""Adzuna India job spider (authorized API, no browser).

Free tier: 10 req/min, paginated 50/page. category=it-jobs gives broad IT
coverage without a keyword query. Yields JobItem; landing handled by the
RawLandingPipeline.
"""

import os
from urllib.parse import urlencode

import scrapy
from dotenv import find_dotenv, load_dotenv
from scrapy.exceptions import CloseSpider

from jobatlas_scrapers.items import JobItem


class AdzunaSpider(scrapy.Spider):
    name = "adzuna"
    allowed_domains = ["api.adzuna.com"]
    custom_settings = {
        # Keys = authorization; robots.txt governs crawlers, not API clients.
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 7.0,  # ~8.5 req/min, under the 10/min cap
    }

    BASE = "https://api.adzuna.com/v1/api/jobs/in/search/{page}"
    RESULTS_PER_PAGE = 50

    def __init__(self, category="it-jobs", max_pages=10, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        self.max_pages = int(max_pages)
        load_dotenv(find_dotenv())
        self.app_id = os.environ.get("ADZUNA_APP_ID")
        self.app_key = os.environ.get("ADZUNA_APP_KEY")

    async def start(self):
        if not self.app_id or not self.app_key:
            raise CloseSpider("ADZUNA_APP_ID / ADZUNA_APP_KEY missing in .env")
        yield self._page_request(1)

    def _page_request(self, page):
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.RESULTS_PER_PAGE,
            "category": self.category,
            "sort_by": "date",
            "content-type": "application/json",
        }
        url = self.BASE.format(page=page) + "?" + urlencode(params)
        return scrapy.Request(url, callback=self.parse, cb_kwargs={"page": page})

    def parse(self, response, page):
        data = response.json()
        results = data.get("results", [])
        for r in results:
            yield self._to_item(r)
        total = data.get("count", 0)
        if results and page < self.max_pages and page * self.RESULTS_PER_PAGE < total:
            yield self._page_request(page + 1)

    def _to_item(self, r):
        smin, smax = r.get("salary_min"), r.get("salary_max")
        salary_text = f"{smin or ''}-{smax or ''}".strip("-") if (smin or smax) else None
        return JobItem(
            source="adzuna",
            source_job_id=str(r["id"]) if r.get("id") is not None else None,
            source_url=r.get("redirect_url"),
            raw_kind="api",
            title=r.get("title"),
            company=(r.get("company") or {}).get("display_name"),
            location=(r.get("location") or {}).get("display_name"),
            salary_text=salary_text,
            posted_date=r.get("created"),
            description=r.get("description"),
            skills=None,
            raw_payload=r,
        )
