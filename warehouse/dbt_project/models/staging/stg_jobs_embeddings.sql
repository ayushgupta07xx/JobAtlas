-- Passthrough: vector(384) lives in pgvector; the API reads it directly.
select * from {{ source('jobatlas', 'jobs_embeddings') }}
