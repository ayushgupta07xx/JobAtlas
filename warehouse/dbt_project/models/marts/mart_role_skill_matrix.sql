-- Skill demand per role bucket: postings per (role, skill).
with rs as (
    select r.role, s.skill_name
    from {{ ref('int_job_role') }} as r
    inner join {{ ref('int_job_skills') }} as s on s.job_id = r.id
)
select
    role,
    skill_name,
    count(*) as job_count
from rs
group by role, skill_name
having count(*) >= 5
order by role, job_count desc
