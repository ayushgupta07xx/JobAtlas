-- Runs on first Postgres container init (entrypoint executes against POSTGRES_DB=jobatlas).

-- pgvector on the jobatlas database
CREATE EXTENSION IF NOT EXISTS vector;

-- Airflow metadata: switch to postgres db, create user + dedicated db
\c postgres
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow_db OWNER airflow;

-- PG 15+ locks down public schema; grant explicitly
\c airflow_db
GRANT ALL ON SCHEMA public TO airflow;
