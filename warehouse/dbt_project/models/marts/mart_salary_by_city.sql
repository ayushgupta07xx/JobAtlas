-- Salary aggregates by city and currency (mixed currencies kept separate).
select
    l.city,
    f.currency,
    count(*) as job_count,
    round(avg(f.salary_min), 0) as avg_salary_min,
    round(avg(f.salary_max), 0) as avg_salary_max,
    min(f.salary_min) as min_salary,
    max(f.salary_max) as max_salary
from {{ ref('fact_jobs') }} as f
inner join {{ ref('dim_location') }} as l on l.location_sk = f.location_sk
where f.salary_min is not null
group by l.city, f.currency
order by job_count desc
