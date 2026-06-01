"""Jobicy job spider (free public API, no key, no browser).

Jobicy is a documented free remote-jobs API; supplementary source per §7.
Single JSON call -> JobItem; landing via RawLandingPipeline into Mongo
raw_api_responses + raw.jobs_raw. Args (all optional): count (default 50),
geo (e.g. india), tag (e.g. python).
"""

from urllib.parse import urlencode

import scrapy

from jobatlas_scrapers.items import JobItem


class JobicySpider(scrapy.Spider):
    name = "jobicy"
    allowed_domains = ["jobicy.com"]
    custom_settings = {
        # Documented public API offered for use -> API client, not a site crawl.
        "ROBOTSTXT_OBEY": False,
    }
    BASE = "https://jobicy.com/api/v2/remote-jobs"

    def __init__(self, count=50, geo="", tag="", *a, **k):
        super().__init__(*a, **k)
        self.count = int(count)
        self.geo = geo
        self.tag = tag

    async def start(self):
        params = {"count": self.count}
        if self.geo:
            params["geo"] = self.geo
        if self.tag:
            params["tag"] = self.tag
        yield scrapy.Request(f"{self.BASE}?{urlencode(params)}", callback=self.parse)

    def parse(self, response):
        data = response.json()
        jobs = data.get("jobs", [])
        if not jobs:
            self.logger.warning(
                "Jobicy: 0 jobs for count=%s geo=%r tag=%r", self.count, self.geo, self.tag
            )
        for j in jobs:
            smin, smax = j.get("annualSalaryMin"), j.get("annualSalaryMax")
            cur = j.get("salaryCurrency") or ""
            salary_text = f"{cur} {smin}-{smax}".strip() if (smin or smax) else None
            yield JobItem(
                source="jobicy",
                source_job_id=str(j["id"]) if j.get("id") is not None else None,
                source_url=j.get("url"),
                raw_kind="api",
                title=j.get("jobTitle"),
                company=j.get("companyName"),
                location=j.get("jobGeo"),
                salary_text=salary_text,
                posted_date=j.get("pubDate"),
                description=j.get("jobDescription") or j.get("jobExcerpt"),
                skills=None,
                raw_payload=j,
            )
