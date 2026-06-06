-- Posting counts and salary coverage by state (state present).
with active as (
    select state, salary_min, currency
    from {{ ref('int_jobs_active') }}
    where state is not null
)
select
    state,
    count(*) as job_count,
    count(salary_min) as jobs_with_salary,
    round(avg(case when currency = 'INR' then salary_min end), 0) as avg_inr_salary_min
from active
group by state
order by job_count desc
