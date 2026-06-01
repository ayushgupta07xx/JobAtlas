"""Naukri recon spider (Playwright).

Naukri is the most aggressively bot-protected source (§19), and its robots.txt
may restrict the search path — which we respect (ROBOTSTXT_OBEY stays on). Recon:
confirm robots allows + the page renders headless without a block/captcha, and
dump the DOM to scrapers/_recon/ for selector authoring.
Run:  scrapy crawl naukri -a url="<naukri search URL from your browser>"
"""

from pathlib import Path

import scrapy
from scrapy_playwright.page import PageMethod


class NaukriSpider(scrapy.Spider):
    name = "naukri"
    allowed_domains = ["naukri.com"]

    def __init__(self, url="https://www.naukri.com/software-developer-jobs", *a, **k):
        super().__init__(*a, **k)
        self.start_url = url

    async def start(self):
        yield scrapy.Request(
            self.start_url,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded"),
                    PageMethod("wait_for_timeout", 5000),
                ],
            },
            callback=self.parse,
            errback=self.errback,
        )

    def parse(self, response):
        out = Path("_recon")
        out.mkdir(exist_ok=True)
        path = out / "naukri.html"
        path.write_text(response.text, encoding="utf-8")
        low = response.text.lower()
        block = any(
            w in low
            for w in (
                "captcha",
                "verify you",
                "access denied",
                "unusual traffic",
                "are you a human",
                "blocked",
            )
        )
        job_links = response.css('a[href*="job-listings"]')
        self.logger.info(
            "RECON naukri: %d bytes -> %s | title=%r | job-listing links=%d | block_signal=%s | login_text=%s",
            len(response.text),
            path,
            response.css("title::text").get(),
            len(job_links),
            block,
            ("log in" in low or "sign in" in low),
        )

    def errback(self, failure):
        self.logger.error("RECON naukri failed: %r", failure.value)
