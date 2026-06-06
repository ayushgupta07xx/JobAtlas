-- Posting counts and salary coverage by role bucket.
with active as (
    select a.id, a.salary_min, r.role
    from {{ ref('int_jobs_active') }} as a
    inner join {{ ref('int_job_role') }} as r on r.id = a.id
)
select
    role,
    count(*) as job_count,
    count(salary_min) as jobs_with_salary,
    round(100.0 * count(salary_min) / count(*), 1) as salary_coverage_pct
from active
group by role
order by job_count desc
