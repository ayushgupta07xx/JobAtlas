-- INR salary aggregates by state.
with active as (
    select state, salary_min, salary_max
    from {{ ref('int_jobs_active') }}
    where state is not null and salary_min is not null and currency = 'INR'
)
select
    state,
    count(*) as job_count,
    round(avg(salary_min), 0) as avg_salary_min,
    round(avg(salary_max), 0) as avg_salary_max
from active
group by state
order by job_count desc
