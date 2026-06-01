"""Scraped item schema shared across all JobAtlas spiders.

Spiders yield a JobItem with best-effort extracted fields plus the full
raw payload. Full normalization into staging.jobs happens in the Day-5
normalizer; the scrape layer only lands raw data + a MinHash signature
for early cross-source dedup.
"""

import scrapy


class JobItem(scrapy.Item):
    # provenance
    source = scrapy.Field()  # "adzuna", "wellfound", "naukri"
    source_url = scrapy.Field()  # canonical posting URL (dedup key with source)
    source_job_id = scrapy.Field()  # source-native job id, when available
    raw_kind = scrapy.Field()  # "api" -> raw_api_responses, "html" -> raw_html

    # best-effort extracted fields (fully normalized on Day 5)
    title = scrapy.Field()
    company = scrapy.Field()
    location = scrapy.Field()  # raw location string
    salary_text = scrapy.Field()  # raw salary string/range, parsed later
    posted_date = scrapy.Field()  # raw date, parsed later
    description = scrapy.Field()
    skills = scrapy.Field()  # list[str] when the source provides them

    # raw payload + integrity
    raw_payload = scrapy.Field()  # original API dict or HTML string, verbatim
    content_hash = scrapy.Field()  # sha256 of raw_payload, set in pipeline

    # dedup + bookkeeping
    minhash_signature = scrapy.Field()  # list[int], computed in pipeline
    fetched_at = scrapy.Field()  # UTC datetime, set in pipeline
