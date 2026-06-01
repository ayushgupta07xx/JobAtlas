with companies as (
    select distinct coalesce(company, 'Unknown') as company_name
    from {{ ref('int_jobs_active') }}
)
select
    {{ dbt_utils.generate_surrogate_key(['company_name']) }} as company_sk,
    company_name
from companies
