-- Salary by role bucket x required-experience band (currencies separate).
with active as (
    select
        a.id, a.salary_min, a.salary_max, a.currency, r.role, e.experience_band
    from {{ ref('int_jobs_active') }} as a
    inner join {{ ref('int_job_role') }} as r on r.id = a.id
    inner join {{ ref('int_job_experience') }} as e on e.id = a.id
)
select
    role,
    experience_band,
    currency,
    count(*) as job_count,
    round(avg(salary_min), 0) as avg_salary_min,
    round(avg(salary_max), 0) as avg_salary_max
from active
where salary_min is not null
group by role, experience_band, currency
order by job_count desc
