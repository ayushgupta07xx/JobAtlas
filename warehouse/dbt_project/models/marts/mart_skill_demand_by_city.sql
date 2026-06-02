-- Skill demand by city (heatmap source).
select
    l.city,
    s.skill_name,
    count(*) as job_count
from {{ ref('bridge_job_skill') }} as b
inner join {{ ref('fact_jobs') }} as f on f.job_sk = b.job_sk
inner join {{ ref('dim_location') }} as l on l.location_sk = f.location_sk
inner join {{ ref('dim_skill') }} as s on s.skill_sk = b.skill_sk
group by l.city, s.skill_name
order by l.city, job_count desc
