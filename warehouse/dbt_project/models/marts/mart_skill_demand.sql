-- Skill demand: job count per skill (dashboard + heatmap source).
select
    s.skill_name,
    count(*) as job_count
from {{ ref('bridge_job_skill') }} as b
inner join {{ ref('dim_skill') }} as s on s.skill_sk = b.skill_sk
group by s.skill_name
order by job_count desc
