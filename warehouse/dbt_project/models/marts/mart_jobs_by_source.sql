-- Job volume by source.
select
    f.source,
    count(*) as job_count
from {{ ref('fact_jobs') }} as f
group by f.source
order by job_count desc
