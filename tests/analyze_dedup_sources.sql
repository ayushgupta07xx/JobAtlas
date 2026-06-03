-- analyze_dedup_sources.sql  (read-only)
-- Splits the deduplicated-out rows into genuine cross-platform alternatives
-- vs same-source clutter (query fan-out / re-posts), and shows real examples.
-- Run:  cat analyze_dedup_sources.sql | docker compose exec -T postgres \
--         sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

-- (1) Grouping-model probe: do KEEPERS carry the group id, or only duplicates?
--     If keepers_with_gid = 0, the cross-source split in (2) undercounts and
--     I need to adjust it -- tell me the number.
SELECT
    count(*) FILTER (WHERE dedup_group_id IS NOT NULL AND NOT is_duplicate) AS keepers_with_gid,
    count(*) FILTER (WHERE dedup_group_id IS NOT NULL AND is_duplicate) AS dups_with_gid
FROM staging.jobs;

-- (2) The split: how many of the 1,409 duplicates are cross-source
--     (a real "apply on your platform" choice) vs same-source noise.
WITH grp AS (
    SELECT
        dedup_group_id,
        count(DISTINCT source) AS n_src
    FROM staging.jobs
    WHERE dedup_group_id IS NOT NULL
    GROUP BY dedup_group_id
)

SELECT
    CASE WHEN g.n_src > 1 THEN 'cross-source' ELSE 'same-source' END AS kind,
    count(*) AS duplicate_rows
FROM staging.jobs AS j
INNER JOIN grp AS g ON j.dedup_group_id = g.dedup_group_id
WHERE j.is_duplicate
GROUP BY kind
ORDER BY duplicate_rows DESC;

-- (3) Sample real cross-source roles: one row per role, the sources it spans.
SELECT
    company,
    left(title, 45) AS title,
    string_agg(DISTINCT source, ', ' ORDER BY source) AS sources,
    count(*) AS copies
FROM staging.jobs
WHERE
    dedup_group_id IN (
        SELECT dedup_group_id
        FROM staging.jobs
        WHERE dedup_group_id IS NOT NULL
        GROUP BY dedup_group_id
        HAVING count(DISTINCT source) > 1
    )
GROUP BY dedup_group_id, company, title
ORDER BY copies DESC
LIMIT 10;
