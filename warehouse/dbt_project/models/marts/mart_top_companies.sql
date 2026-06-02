-- Companies ranked by number of open postings.
select
    c.company_name,
    count(*) as job_count
from {{ ref('fact_jobs') }} as f
inner join {{ ref('dim_company') }} as c on c.company_sk = f.company_sk
group by c.company_name
order by job_count desc
