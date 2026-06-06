-- Per-source coverage: active postings, salary fill rate, latest posting.
with active as (
    select source, salary_min, posted_date from {{ ref('int_jobs_active') }}
)
select
    source,
    count(*) as job_count,
    count(salary_min) as jobs_with_salary,
    round(100.0 * count(salary_min) / count(*), 1) as salary_coverage_pct,
    max(posted_date) as latest_posting
from active
group by source
order by job_count desc
