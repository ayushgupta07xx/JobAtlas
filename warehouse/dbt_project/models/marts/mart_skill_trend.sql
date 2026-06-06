-- Monthly demand per skill (postings mentioning the skill, by posted month).
with sk as (
    select s.job_id, s.skill_name, a.posted_date
    from {{ ref('int_job_skills') }} as s
    inner join {{ ref('int_jobs_active') }} as a on a.id = s.job_id
    where a.posted_date is not null
)
select
    skill_name,
    date_trunc('month', posted_date) as posted_month,
    count(*) as job_count
from sk
group by skill_name, date_trunc('month', posted_date)
order by posted_month desc, job_count desc
