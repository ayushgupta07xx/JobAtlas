-- Postings per day (hiring velocity over time).
select
    f.posted_date,
    count(*) as jobs_posted
from {{ ref('fact_jobs') }} as f
where f.posted_date is not null
group by f.posted_date
order by f.posted_date
