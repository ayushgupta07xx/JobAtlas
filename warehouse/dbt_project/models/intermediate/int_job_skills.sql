-- Postgres unnests the live skills array; other targets read the pre-unnested seed.
{% if target.name == 'postgres' %}
with active as (
    select id, skills from {{ ref('int_jobs_active') }}
)
select
    a.id                  as job_id,
    lower(trim(s.skill))  as skill_name
from active a
cross join lateral unnest(a.skills) as s(skill)
where s.skill is not null and trim(s.skill) <> ''
{% else %}
select
    job_id,
    skill_name
from {{ ref('job_skills_seed') }}
{% endif %}
