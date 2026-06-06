-- Flat per-job feature base for the salary regression (INR, salaried only).
select
    a.id,
    a.salary_min,
    a.salary_max,
    a.city,
    a.state,
    a.country,
    a.source,
    r.role,
    e.experience_min,
    e.experience_band,
    a.posted_date
from {{ ref('int_jobs_active') }} as a
inner join {{ ref('int_job_role') }} as r on r.id = a.id
inner join {{ ref('int_job_experience') }} as e on e.id = a.id
where a.salary_min is not null and a.currency = 'INR'
