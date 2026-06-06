-- Monthly posting volume per company.
with active as (
    select company, posted_date
    from {{ ref('int_jobs_active') }}
    where company is not null and posted_date is not null
)
select
    company,
    date_trunc('month', posted_date) as posted_month,
    count(*) as job_count
from active
group by company, date_trunc('month', posted_date)
order by posted_month desc, job_count desc
