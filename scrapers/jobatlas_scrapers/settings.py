"""Scrapy settings for the JobAtlas scrapers project.

One Scrapy project, one spider per source (ADR-0003). Polite by default:
robots.txt obeyed, 1 request / 5s per domain, autothrottle on, rotating
user-agents. JS-heavy sources render via scrapy-playwright; the Adzuna
API spider needs no browser.
"""

BOT_NAME = "jobatlas_scrapers"

SPIDER_MODULES = ["jobatlas_scrapers.spiders"]
NEWSPIDER_MODULE = "jobatlas_scrapers.spiders"

# --- Politeness (JobAtlas.md §7, §21 rule 6) -------------------------------
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 5.0  # 1 request / 5s on scraped domains
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # never overlap within a domain
RANDOMIZE_DOWNLOAD_DELAY = True

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# --- User-agent rotation (middlewares.py) ----------------------------------
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "jobatlas_scrapers.middlewares.RotateUserAgentMiddleware": 400,
}

# --- Playwright (JS-heavy sources) -----------------------------------------
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "args": ["--disable-blink-features=AutomationControlled"],
}
# Real Chrome fingerprint so JS-heavy sites do not 403 the headless
# context (UA + viewport + locale drive navigator.*).
PLAYWRIGHT_CONTEXTS = {
    "default": {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1366, "height": 768},
        "locale": "en-US",
    }
}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # ms

# --- Item pipelines --------------------------------------------------------
# Enabled in the next batch once pipelines.py lands (MinHash -> Mongo ->
# raw.jobs_raw). Commented so a premature crawl doesn't import a missing module.
ITEM_PIPELINES = {
    "jobatlas_scrapers.pipelines.RawLandingPipeline": 300,
}

# --- Misc ------------------------------------------------------------------
LOG_LEVEL = "INFO"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"
