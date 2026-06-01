with skills as (
    select distinct skill_name from {{ ref('int_job_skills') }}
)
select
    {{ dbt_utils.generate_surrogate_key(['skill_name']) }} as skill_sk,
    skill_name
from skills
