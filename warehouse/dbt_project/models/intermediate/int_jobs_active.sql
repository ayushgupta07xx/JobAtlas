-- Canonical analytical set: active, non-duplicate postings.
select *
from {{ ref('stg_jobs') }}
where coalesce(is_active, true) = true
  and coalesce(is_duplicate, false) = false
