-- Grain: one row per (job, skill). Resolves the many-to-many.
select
    {{ dbt_utils.generate_surrogate_key(['js.job_id']) }} as job_sk,
    ds.skill_sk
from {{ ref('int_job_skills') }} js
inner join {{ ref('dim_skill') }} ds on ds.skill_name = js.skill_name
