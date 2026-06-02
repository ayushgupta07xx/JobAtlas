-- pgvector-only source; not part of the warehouse star (the API reads embeddings
-- directly from Postgres). Disabled on non-Postgres targets.
{{ config(enabled = (target.name == 'postgres')) }}
select * from {{ source('jobatlas', 'jobs_embeddings') }}
