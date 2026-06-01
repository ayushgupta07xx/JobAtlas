with locations as (
    select distinct
        coalesce(city, 'Unknown')    as city,
        coalesce(state, 'Unknown')   as state,
        coalesce(country, 'ZZ')      as country
    from {{ ref('int_jobs_active') }}
)
select
    {{ dbt_utils.generate_surrogate_key(['city', 'state', 'country']) }} as location_sk,
    city,
    state,
    country
from locations
