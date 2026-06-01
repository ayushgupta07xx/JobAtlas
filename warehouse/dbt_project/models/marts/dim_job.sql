-- SCD Type 2 job dimension. Full history in snapshots.dim_job_snapshot.
-- is_current flags the live version; job_sk joins to fact_jobs.
select
    {{ dbt_utils.generate_surrogate_key(['id', 'dbt_valid_from']) }} as job_version_sk,
    {{ dbt_utils.generate_surrogate_key(['id']) }}                   as job_sk,
    id as job_id,
    title,
    company,
    salary_min,
    salary_max,
    currency,
    city,
    state,
    country,
    posted_date,
    dbt_valid_from,
    dbt_valid_to,
    (dbt_valid_to is null) as is_current
from {{ ref('dim_job_snapshot') }}
