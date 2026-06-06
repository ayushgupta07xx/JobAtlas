-- Salary aggregates by required-experience band (currencies kept separate).
with active as (
    select a.id, a.salary_min, a.salary_max, a.currency, e.experience_band
    from {{ ref('int_jobs_active') }} as a
    inner join {{ ref('int_job_experience') }} as e on e.id = a.id
)
select
    experience_band,
    currency,
    count(*) as job_count,
    round(avg(salary_min), 0) as avg_salary_min,
    round(avg(salary_max), 0) as avg_salary_max,
    min(salary_min) as min_salary,
    max(salary_max) as max_salary
from active
where salary_min is not null
group by experience_band, currency
order by job_count desc
