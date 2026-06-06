-- Required-experience band per active job (drives experience analytics).
select
    id,
    experience_min,
    experience_max,
    case
        when experience_min is null then 'Not specified'
        when experience_min <= 2 then 'Entry (0-2)'
        when experience_min <= 5 then 'Mid (3-5)'
        when experience_min <= 10 then 'Senior (6-10)'
        else 'Lead (10+)'
    end as experience_band
from {{ ref('int_jobs_active') }}
