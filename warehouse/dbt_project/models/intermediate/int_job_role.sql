-- Coarse role bucket from the job title (keyword precedence, first match wins).
with active as (
    select id, title, lower(title) as title_l
    from {{ ref('int_jobs_active') }}
)
select
    id,
    title,
    case
        when title_l like '%data engineer%' then 'Data Engineer'
        when title_l like '%data scientist%' then 'Data Scientist'
        when title_l like '%machine learning%' then 'ML Engineer'
        when title_l like '%ml engineer%' then 'ML Engineer'
        when title_l like '%data analyst%' then 'Data Analyst'
        when title_l like '%product analyst%' then 'Product Analyst'
        when title_l like '%business analyst%' then 'Business Analyst'
        when title_l like '%analytics%' then 'Analytics'
        when title_l like '%devops%' then 'DevOps / SRE'
        when title_l like '%sre%' then 'DevOps / SRE'
        when title_l like '%platform engineer%' then 'DevOps / SRE'
        when title_l like '%full stack%' then 'Full Stack'
        when title_l like '%fullstack%' then 'Full Stack'
        when title_l like '%frontend%' then 'Frontend'
        when title_l like '%backend%' then 'Backend'
        when title_l like '%product manager%' then 'Product Manager'
        when title_l like '%software engineer%' then 'Software Engineer'
        when title_l like '%developer%' then 'Software Engineer'
        else 'Other'
    end as role
from active
