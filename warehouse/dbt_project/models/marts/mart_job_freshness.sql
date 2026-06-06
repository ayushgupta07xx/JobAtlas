-- Posting freshness buckets by age in days from today.
with active as (
    select current_date - posted_date as age_days
    from {{ ref('int_jobs_active') }}
    where posted_date is not null
),
bucketed as (
    select
        age_days,
        case
            when age_days <= 7 then '0-7 days'
            when age_days <= 30 then '8-30 days'
            when age_days <= 90 then '31-90 days'
            else '90+ days'
        end as freshness_bucket
    from active
)
select
    freshness_bucket,
    count(*) as job_count,
    min(age_days) as min_age_days
from bucketed
group by freshness_bucket
order by min_age_days
