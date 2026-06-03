"""Adzuna India tech job spider (authorized API, no browser).

Free tier: 25 req/min, 250/day, 2500/month. We fan out across India tech
hubs (where) x tech role families (what), every query pinned to
category=it-jobs so the index stays tech-only. A global request budget
hard-stops under the daily cap, and we drop repeat job-ids in-run so the
fan-out never double-counts. Yields JobItem; landing via RawLandingPipeline.
"""

import os
from urllib.parse import urlencode

import scrapy
from dotenv import find_dotenv, load_dotenv
from scrapy.exceptions import CloseSpider

from jobatlas_scrapers.items import JobItem

# "" = nationwide pass (catches anything the city tags miss).
DEFAULT_WHERE = [
    "",
    "Bangalore",
    "Mumbai",
    "Delhi",
    "Hyderabad",
    "Pune",
    "Chennai",
    "Gurgaon",
    "Noida",
    "Kolkata",
]

# Tech role families. Pinned under category=it-jobs, so these only deepen
# coverage within tech - they never pull in non-tech roles.
DEFAULT_WHAT = [
    "",
    "software engineer",
    "data engineer",
    "data analyst",
    "data scientist",
    "backend developer",
    "frontend developer",
    "full stack developer",
    "devops engineer",
    "machine learning engineer",
    "python developer",
    "java developer",
    "qa engineer",
    "android developer",
    "cloud engineer",
    "business analyst",
    "product analyst",
]


class AdzunaSpider(scrapy.Spider):
    name = "adzuna"
    allowed_domains = ["api.adzuna.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 3.0,  # ~20 req/min, under the 25/min cap
    }

    BASE = "https://api.adzuna.com/v1/api/jobs/in/search/{page}"
    RESULTS_PER_PAGE = 50

    def __init__(
        self,
        category="it-jobs",
        max_pages=3,
        max_requests=240,
        where=None,
        what=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.category = category
        self.max_pages = int(max_pages)
        self.max_requests = int(max_requests)
        self.where_list = where.split("|") if where else DEFAULT_WHERE
        self.what_list = what.split("|") if what else DEFAULT_WHAT
        self._requests_made = 0
        self._seen_ids = set()
        load_dotenv(find_dotenv())
        self.app_id = os.environ.get("ADZUNA_APP_ID")
        self.app_key = os.environ.get("ADZUNA_APP_KEY")

    async def start(self):
        if not self.app_id or not self.app_key:
            raise CloseSpider("ADZUNA_APP_ID / ADZUNA_APP_KEY missing in .env")
        for where in self.where_list:
            for what in self.what_list:
                req = self._page_request(1, what=what, where=where)
                if req is None:
                    return
                yield req

    def _page_request(self, page, what, where):
        if self._requests_made >= self.max_requests:
            self.logger.info("adzuna: request budget %d hit, stopping", self.max_requests)
            return None
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.RESULTS_PER_PAGE,
            "category": self.category,
            "sort_by": "date",
            "content-type": "application/json",
        }
        if what:
            params["what"] = what
        if where:
            params["where"] = where
        url = self.BASE.format(page=page) + "?" + urlencode(params)
        self._requests_made += 1
        return scrapy.Request(
            url,
            callback=self.parse,
            cb_kwargs={"page": page, "what": what, "where": where},
        )

    def parse(self, response, page, what, where):
        data = response.json()
        results = data.get("results", [])
        for r in results:
            jid = str(r.get("id"))
            if jid in self._seen_ids:
                continue
            self._seen_ids.add(jid)
            yield self._to_item(r)
        total = data.get("count", 0)
        if results and page < self.max_pages and page * self.RESULTS_PER_PAGE < total:
            req = self._page_request(page + 1, what=what, where=where)
            if req is not None:
                yield req

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
