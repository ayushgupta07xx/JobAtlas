-- Salary aggregates by role bucket (currencies kept separate).
with active as (
    select a.id, a.salary_min, a.salary_max, a.currency, r.role
    from {{ ref('int_jobs_active') }} as a
    inner join {{ ref('int_job_role') }} as r on r.id = a.id
)
select
    role,
    currency,
    count(*) as job_count,
    round(avg(salary_min), 0) as avg_salary_min,
    round(avg(salary_max), 0) as avg_salary_max
from active
where salary_min is not null
group by role, currency
order by job_count desc
