-- Skill-pair co-occurrence across postings (skill_a < skill_b dedupes pairs).
-- Feeds the skill-affinity / clustering narrative.
with sk as (
    select job_id, skill_name from {{ ref('int_job_skills') }}
)
select
    s1.skill_name as skill_a,
    s2.skill_name as skill_b,
    count(*) as co_count
from sk as s1
inner join sk as s2
    on s1.job_id = s2.job_id and s1.skill_name < s2.skill_name
group by s1.skill_name, s2.skill_name
having count(*) >= 10
order by co_count desc
