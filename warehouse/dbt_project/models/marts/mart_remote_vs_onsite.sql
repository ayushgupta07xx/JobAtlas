-- Remote/worldwide (country ZZ) vs located postings: counts and INR salary.
with active as (
    select
        case
            when country = 'ZZ' then 'Remote / Worldwide' else 'Located'
        end as work_mode,
        salary_min,
        currency
    from {{ ref('int_jobs_active') }}
)
select
    work_mode,
    count(*) as job_count,
    round(avg(case when currency = 'INR' then salary_min end), 0) as avg_inr_salary_min
from active
group by work_mode
order by job_count desc
