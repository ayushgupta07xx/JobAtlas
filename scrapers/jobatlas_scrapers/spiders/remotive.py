"""Remotive public API spider (no key).

GET https://remotive.com/api/remote-jobs?limit=N -> {"jobs": [...]}. Remotive's
terms are strict: mandatory link-back + attribution, jobs are 24h-delayed at the
source, and they must NOT sit behind a signup / email-collection flow. We honor
all of that in code via the sources registry (remotive => exclude_from_match,
attribution_required, apply_url -> source_url) rather than a user-facing
disclaimer -- a disclaimer does not cure a duty owed to the platform.

India-eligibility is read straight off `candidate_required_location`
("Worldwide" / "India" / "USA Only" / ...): keep worldwide / India / APAC,
drop country-locked-elsewhere.

    scrapy crawl remotive
"""

import scrapy

from jobatlas_scrapers.ats_common import clean_text, is_india_location
from jobatlas_scrapers.items import JobItem


class RemotiveSpider(scrapy.Spider):
    name = "remotive"
    allowed_domains = ["remotive.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # documented public API offered for consumption
        "DOWNLOAD_DELAY": 1.0,
    }
    URL = "https://remotive.com/api/remote-jobs?limit=1000"

    async def start(self):
        yield scrapy.Request(self.URL, callback=self.parse, dont_filter=True)

    def parse(self, response):
        jobs = response.json().get("jobs", [])
        kept = 0
        for j in jobs:
            crl = (j.get("candidate_required_location") or "").strip()
            # blank == worldwide == India-eligible
            if crl and not is_india_location(crl):
                continue
            yield JobItem(
                source="remotive",
                source_job_id=str(j.get("id")) if j.get("id") is not None else None,
                source_url=j.get("url"),
                raw_kind="api",
                title=j.get("title"),
                company=j.get("company_name"),
                location=crl or "Worldwide",
                salary_text=j.get("salary"),
                posted_date=j.get("publication_date"),
                description=clean_text(j.get("description")),
                skills=None,
                raw_payload=j,
            )
            kept += 1
        self.logger.info("remotive: kept %d/%d India-eligible roles", kept, len(jobs))
