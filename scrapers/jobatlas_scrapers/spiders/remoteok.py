"""RemoteOK public API spider (single JSON endpoint, no key).

GET https://remoteok.com/api -> JSON array; element 0 is a legal/metadata
object, the rest are jobs. Public feed; RemoteOK asks for attribution + a
link-back, honored via the sources registry + the frontend (apply -> source_url).

Keep India-eligible roles only: a blank location means worldwide-remote (an
India-based dev can take it); a named location must be India / global / APAC.
A US-only / EU-only remote role is dropped.

    scrapy crawl remoteok

If RemoteOK answers 403 / a Cloudflare challenge, that is bot protection: we
respect it (no UA spoofing beyond the normal rotation, no proxies) and treat
the source as best-effort -- it just lands 0 and we lean on the other feeds.
"""

import scrapy

from jobatlas_scrapers.ats_common import clean_text, is_india_location
from jobatlas_scrapers.items import JobItem


class RemoteOKSpider(scrapy.Spider):
    name = "remoteok"
    allowed_domains = ["remoteok.com"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # documented public API offered for consumption
        "DOWNLOAD_DELAY": 1.0,
    }
    URL = "https://remoteok.com/api"

    async def start(self):
        yield scrapy.Request(self.URL, callback=self.parse, dont_filter=True)

    def parse(self, response):
        rows = response.json()
        jobs = [r for r in rows if isinstance(r, dict) and r.get("id")]
        kept = 0
        for j in jobs:
            loc = (j.get("location") or "").strip()
            tags = " ".join(j.get("tags") or [])
            # blank location == worldwide remote == India-eligible
            if loc and not is_india_location(loc, tags):
                continue
            yield JobItem(
                source="remoteok",
                source_job_id=str(j.get("id")),
                source_url=j.get("url"),
                raw_kind="api",
                title=j.get("position") or j.get("title"),
                company=j.get("company"),
                location=loc or "Worldwide",
                salary_text=None,
                posted_date=j.get("date"),
                description=clean_text(j.get("description")),
                skills=None,
                raw_payload=j,
            )
            kept += 1
        self.logger.info("remoteok: kept %d/%d India-eligible roles", kept, len(jobs))
