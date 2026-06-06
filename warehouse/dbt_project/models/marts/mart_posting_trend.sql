-- Daily posting volume (active postings by posted date).
select
    posted_date,
    count(*) as job_count
from {{ ref('int_jobs_active') }}
where posted_date is not null
group by posted_date
order by posted_date desc
