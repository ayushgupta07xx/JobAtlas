-- Grain: one row per active, non-duplicate job posting.
-- dim_job (SCD2) FK lands Day 9 via snapshot.
with jobs as (
    select * from {{ ref('int_jobs_active') }}
)
select
    {{ dbt_utils.generate_surrogate_key(['id']) }}                          as job_sk,
    id                                                                      as job_id,
    {{ dbt_utils.generate_surrogate_key(["coalesce(company, 'Unknown')"]) }} as company_sk,
    {{ dbt_utils.generate_surrogate_key([
        "coalesce(city, 'Unknown')",
        "coalesce(state, 'Unknown')",
        "coalesce(country, 'ZZ')"
    ]) }}                                                                   as location_sk,
    cast(to_char(posted_date, 'YYYYMMDD') as integer)                       as posted_date_key,
    source,
    source_job_id,
    source_url,
    title,
    salary_min,
    salary_max,
    currency,
    posted_date,
    dedup_group_id,
    scraped_at
from jobs
