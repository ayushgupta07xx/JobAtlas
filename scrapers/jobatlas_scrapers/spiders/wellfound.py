"""Wellfound India job spider (Playwright).

Renders the JS listing via scrapy-playwright (the real Chrome fingerprint in
settings clears the bot 403), then yields one item per job row. Company comes
from the parent company block's /company/ link. Salary/location/date are
best-effort; the Day-5 normalizer does full parsing from the landed row HTML,
which is stored verbatim in Mongo raw_html via the RawLandingPipeline.
"""

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import scrapy
from scrapy_playwright.page import PageMethod

from jobatlas_scrapers.items import JobItem

JOB_HREF_RE = re.compile(r"/jobs/(\d+)")
DATE_HINTS = ("ago", "day", "week", "month", "hour", "minute", "yesterday", "today")


class WellfoundSpider(scrapy.Spider):
    name = "wellfound"
    allowed_domains = ["wellfound.com"]

    def __init__(self, url="https://wellfound.com/location/india", max_pages=10, *a, **k):
        super().__init__(*a, **k)
        self.start_url = url
        self.max_pages = int(max_pages)

    async def start(self):
        yield self._page_request(self.start_url, 1)

    def _page_request(self, url, page):
        return scrapy.Request(
            url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded"),
                    PageMethod("wait_for_timeout", 4000),
                ],
            },
            callback=self.parse,
            cb_kwargs={"page": page},
            errback=self.errback,
        )

    def parse(self, response, page):
        count = 0
        for a in response.css('a[href*="/jobs/"]'):
            href = a.attrib.get("href", "")
            m = JOB_HREF_RE.search(href)
            if not m:
                continue  # skip nav / signup links
            count += 1
            row = a.xpath('ancestor::div[contains(@class,"min-h-")][1]')
            block = a.xpath(
                'ancestor::div[contains(@class,"rounded") and contains(@class,"border")][1]'
            )
            comp_texts = block.css('a[href*="/company/"] ::text').getall()
            company = next((t.strip() for t in comp_texts if t.strip()), None)

            salary_text = location = posted_date = None
            for d in row.css("div.flex.items-center"):
                txt = " ".join(t.strip() for t in d.css("::text").getall() if t.strip())
                if not txt:
                    continue
                low = txt.lower()
                if any(h in low for h in DATE_HINTS):
                    posted_date = posted_date or txt
                elif re.search(r"[\$₹]|\d+\s*[kK]\b|\d+\s*[-–]\s*\d", txt):
                    salary_text = salary_text or txt
                else:
                    location = location or txt

            yield JobItem(
                source="wellfound",
                source_job_id=m.group(1),
                source_url=response.urljoin(href),
                raw_kind="html",
                title=(a.css("::text").get() or "").strip(),
                company=company,
                location=location,
                salary_text=salary_text,
                posted_date=posted_date,
                description=None,
                skills=None,
                raw_payload=row.get() or a.get(),
            )

        if count == 0:
            self.logger.warning(
                "Wellfound page %d: 0 jobs parsed — selectors may have drifted", page
            )

        total = self._total_pages(response.text)
        if page < self.max_pages and page < total:
            yield self._page_request(self._with_page(self.start_url, page + 1), page + 1)

    @staticmethod
    def _total_pages(text):
        m = re.search(r"Page\s+\d+\s+of\s+(\d+)", text)
        return int(m.group(1)) if m else 1

    @staticmethod
    def _with_page(url, page):
        parts = urlparse(url)
        q = parse_qs(parts.query)
        q["page"] = [str(page)]
        return urlunparse(parts._replace(query=urlencode(q, doseq=True)))

    def errback(self, failure):
        self.logger.error("Wellfound request failed: %r", failure.value)
