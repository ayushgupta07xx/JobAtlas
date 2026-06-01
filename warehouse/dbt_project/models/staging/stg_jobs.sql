with source as (
    select * from {{ source('jobatlas', 'jobs') }}
)
select
    id,
    raw_id,
    source,
    source_job_id,
    source_url,
    nullif(trim(title), '')    as title,
    nullif(trim(company), '')  as company,
    nullif(trim(city), '')     as city,
    nullif(trim(state), '')    as state,
    nullif(trim(country), '')  as country,
    salary_min,
    salary_max,
    nullif(trim(currency), '') as currency,
    posted_date,
    description,
    skills,
    content_hash,
    is_active,
    is_duplicate,
    dedup_group_id,
    scraped_at,
    created_at,
    updated_at
from source
