"""Downloader middlewares for JobAtlas spiders."""

import random

from scrapy import signals

# Realistic desktop UAs, rotated per request to avoid trivial UA blocking.
# NOTE: this covers the non-Playwright path (Adzuna API). Playwright-rendered
# spiders (Naukri, Wellfound) set their UA via the browser context instead.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) " "Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]


class RotateUserAgentMiddleware:
    """Assign a random User-Agent to each outgoing request."""

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls()
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        return mw

    def process_request(self, request, spider):
        request.headers["User-Agent"] = random.choice(USER_AGENTS)
        return None

    def spider_opened(self, spider):
        spider.logger.info("RotateUserAgentMiddleware active (%d UAs)", len(USER_AGENTS))
