-- Skills rising in share: last-30-day mentions vs the prior 30-day window.
with sk as (
    select s.skill_name, a.posted_date
    from {{ ref('int_job_skills') }} as s
    inner join {{ ref('int_jobs_active') }} as a on a.id = s.job_id
    where a.posted_date is not null
),
windowed as (
    select
        skill_name,
        sum(case
            when posted_date >= current_date - 30 then 1 else 0
        end) as recent_count,
        sum(case
            when posted_date >= current_date - 60
                and posted_date < current_date - 30 then 1 else 0
        end) as prior_count
    from sk
    group by skill_name
)
select
    skill_name,
    recent_count,
    prior_count,
    recent_count - prior_count as delta
from windowed
where recent_count >= 5
order by delta desc
