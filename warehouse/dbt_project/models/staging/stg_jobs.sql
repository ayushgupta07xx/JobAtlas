-- Postgres reads the live source; other targets read the seed (multi-warehouse demo).
with source as (
    {% if target.name == 'postgres' %}
    select * from {{ source('jobatlas', 'jobs') }}
    {% else %}
    select * from {{ ref('jobs_seed') }}
    {% endif %}
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
    {% if target.name == 'postgres' %}
    experience_min,
    experience_max,
    {% else %}
    cast(null as integer) as experience_min,
    cast(null as integer) as experience_max,
    {% endif %}
    {% if target.name == 'postgres' %}
    skills,
    {% else %}
    cast(null as varchar) as skills,
    {% endif %}
    content_hash,
    is_active,
    is_duplicate,
    dedup_group_id,
    scraped_at,
    created_at,
    updated_at
from source
