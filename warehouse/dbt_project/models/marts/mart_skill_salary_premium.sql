-- Average advertised INR salary for postings mentioning each skill, to surface
-- skill salary premiums (>=5 postings to drop noise). Backs the regression story.
with sk as (
    select s.skill_name, a.salary_min, a.salary_max
    from {{ ref('int_job_skills') }} as s
    inner join {{ ref('int_jobs_active') }} as a on a.id = s.job_id
    where a.salary_min is not null and a.currency = 'INR'
)
select
    skill_name,
    count(*) as job_count,
    round(avg(salary_min), 0) as avg_salary_min,
    round(avg(salary_max), 0) as avg_salary_max
from sk
group by skill_name
having count(*) >= 5
order by avg_salary_max desc
