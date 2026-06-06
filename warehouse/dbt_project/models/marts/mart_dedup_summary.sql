-- Deduplication summary by source: duplicate rows vs total (MinHash dedup).
with j as (
    select source, is_duplicate from {{ ref('stg_jobs') }}
)
select
    source,
    count(*) as total_rows,
    sum(case when is_duplicate then 1 else 0 end) as duplicate_rows,
    round(
        100.0 * sum(case when is_duplicate then 1 else 0 end) / count(*), 1
    ) as duplicate_pct
from j
group by source
order by total_rows desc
