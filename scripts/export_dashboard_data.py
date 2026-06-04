import csv
import os

import psycopg2

OUT = "docs/dashboards"
os.makedirs(OUT, exist_ok=True)

ROLE = """case
  when title ilike '%data engineer%' then 'Data Engineer'
  when title ilike '%data analyst%' or title ilike '%data analytics%'
    then 'Data Analyst'
  when title ilike '%business analyst%' then 'Business Analyst'
  when title ilike '%data scientist%' or title ilike '%machine learning%'
    or title ilike '%ml engineer%' then 'Data Science / ML'
  when title ilike '%analyst%' or title ilike '%analytics%'
    then 'Analytics / BI'
  when title ilike '%devops%' or title ilike '%sre%'
    or title ilike '%platform%' then 'DevOps / SRE'
  when title ilike '%full stack%' or title ilike '%fullstack%'
    or title ilike '%full-stack%' then 'Full Stack'
  when title ilike '%frontend%' or title ilike '%front end%' then 'Frontend'
  when title ilike '%backend%' or title ilike '%back end%' then 'Backend'
  when title ilike '%software%' or title ilike '%developer%'
    or title ilike '%engineer%' or title ilike '%sde%'
    then 'Software Engineering'
  else 'Other'
end"""

SEN = """case
  when title ilike '%intern%' then '1 Intern'
  when title ilike '%fresher%' or title ilike '%trainee%'
    or title ilike '%graduate%' or title ilike '%junior%'
    or title ilike '%entry%' then '2 Junior'
  when title ilike '%principal%' or title ilike '%staff%'
    or title ilike '%lead%' or title ilike '%architect%'
    or title ilike '%head%' or title ilike '%manager%'
    or title ilike '%director%' then '5 Lead+'
  when title ilike '%senior%' or title ilike '%sr %' then '4 Senior'
  else '3 Mid'
end"""

JOBS_Q = f"""
select
  title,
  {ROLE} as role_family,
  {SEN} as seniority,
  company, city, state, source,
  salary_min, salary_max,
  case when salary_min is not null and salary_max is not null
    then round((salary_min + salary_max) / 2.0, 0) end as salary_mid,
  currency, posted_date, scraped_at
from staging.jobs
where is_active = true and is_duplicate = false
"""

SKILLS_Q = """
with top_skills as (
  select s as skill, count(*) c
  from staging.jobs, unnest(skills) s
  where is_active = true and is_duplicate = false
  group by s order by c desc limit 30
)
select s as skill, city, count(*) as n
from staging.jobs, unnest(skills) s
where is_active = true and is_duplicate = false
  and s in (select skill from top_skills)
  and city is not null and city <> ''
group by s, city
order by skill, n desc
"""


def to_csv(cur, query, path):
    cur.execute(query)
    cols = [d[0] for d in cur.description]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        n = 0
        for row in cur.fetchall():
            w.writerow(row)
            n += 1
    print(f"wrote {path}: {n} rows")


conn = psycopg2.connect(os.environ["NEON_URL"])
cur = conn.cursor()
to_csv(cur, JOBS_Q, f"{OUT}/jobs_extract.csv")
to_csv(cur, SKILLS_Q, f"{OUT}/skills_by_city.csv")

print("\n=== KPI SUMMARY (for Looker Executive View) ===")
cur.execute("select count(*) from staging.jobs where is_active and not is_duplicate")
print("jobs_indexed (active, non-dup):", cur.fetchone()[0])
cur.execute(
    "select round(100.0 * count(*) filter (where is_duplicate) "
    "/ nullif(count(*), 0), 1) from staging.jobs where is_active"
)
print("duplicate_rate_pct (of active):", cur.fetchone()[0])
cur.execute(
    "select round(100.0 * count(*) filter "
    "(where posted_date >= current_date - interval '30 days') "
    "/ nullif(count(*), 0), 1) from staging.jobs "
    "where is_active and not is_duplicate"
)
print("posted_last_30d_pct:", cur.fetchone()[0])
cur.execute("select max(posted_date), max(scraped_at) from staging.jobs where is_active")
mp, ms = cur.fetchone()
print("newest_posted_date:", mp)
print("newest_scraped_at:", ms)
print("match_latency_p95_ms (from bench, constant): 5.99")

cur.close()
conn.close()
