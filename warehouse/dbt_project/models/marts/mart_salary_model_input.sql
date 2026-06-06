-- Materialized salary-regression input: features + skill_count + salary midpoint.
with feat as (
    select * from {{ ref('int_salary_features') }}
),
skill_counts as (
    select job_id, count(*) as skill_count
    from {{ ref('int_job_skills') }}
    group by job_id
)
select
    f.id,
    f.salary_min,
    f.salary_max,
    (f.salary_min + f.salary_max) / 2 as salary_mid,
    f.city,
    f.state,
    f.country,
    f.source,
    f.role,
    f.experience_min,
    f.experience_band,
    coalesce(sc.skill_count, 0) as skill_count,
    f.posted_date
from feat as f
left join skill_counts as sc on sc.job_id = f.id
