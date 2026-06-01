-- Grain: one row per (job, skill). Unnests the skills TEXT[] array.
with active as (
    select id, skills from {{ ref('int_jobs_active') }}
)
select
    a.id                  as job_id,
    lower(trim(s.skill))  as skill_name
from active a
cross join lateral unnest(a.skills) as s(skill)
where s.skill is not null and trim(s.skill) <> ''
