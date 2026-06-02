"""Build and run Great Expectations suites for JobAtlas (GX 1.x, file context).

Targets local Postgres: staging.jobs, marts.fact_jobs, marts.dim_company.
Idempotent: re-running rebuilds suites/validations/checkpoint from this file.
To fully reset: rm -rf warehouse/great_expectations/gx, then re-run.
"""

import os
import sys

import great_expectations as gx
from dotenv import load_dotenv
from great_expectations import expectations as gxe

load_dotenv()

GX_ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCES = ["adzuna", "jobicy", "wellfound", "naukri", "hirist", "instahyre", "indeed"]
SALARY_MAX = 100000000


def pg_url():
    url = os.environ["DATABASE_URL"]
    if "+psycopg2" not in url:
        url = url.replace("+psycopg", "+psycopg2")
    if "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://")
    return url


def add_or_get_datasource(context, name, url):
    try:
        return context.data_sources.add_postgres(name, connection_string=url)
    except Exception:
        return context.data_sources.get(name)


def add_or_get_asset(ds, name, table, schema):
    try:
        return ds.add_table_asset(name=name, table_name=table, schema_name=schema)
    except Exception:
        return ds.get_asset(name)


def add_or_get_batch_def(asset, name):
    try:
        return asset.add_batch_definition_whole_table(name)
    except Exception:
        return asset.get_batch_definition(name)


def safe_delete(factory, name):
    calls = (
        lambda: factory.delete(name),
        lambda: factory.delete(name=name),
        lambda: factory.delete(factory.get(name)),
    )
    for call in calls:
        try:
            call()
            return
        except TypeError:
            continue
        except Exception:
            return


def staging_jobs_expectations():
    return [
        gxe.ExpectTableRowCountToBeBetween(min_value=300, max_value=20000),
        gxe.ExpectColumnValuesToNotBeNull(column="id"),
        gxe.ExpectColumnValuesToBeUnique(column="id"),
        gxe.ExpectColumnValuesToNotBeNull(column="source"),
        gxe.ExpectColumnValuesToNotBeNull(column="source_url"),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
        gxe.ExpectColumnValuesToNotBeNull(column="scraped_at"),
        gxe.ExpectColumnValuesToBeInSet(column="source", value_set=SOURCES),
        gxe.ExpectColumnValuesToMatchRegex(column="source_url", regex="^https?://"),
        gxe.ExpectColumnValuesToBeBetween(column="salary_min", min_value=0, max_value=SALARY_MAX),
        gxe.ExpectColumnValuesToBeBetween(column="salary_max", min_value=0, max_value=SALARY_MAX),
        gxe.ExpectColumnValuesToNotBeNull(column="is_active"),
        gxe.ExpectColumnValuesToNotBeNull(column="is_duplicate"),
    ]


def fact_jobs_expectations():
    return [
        gxe.ExpectTableRowCountToBeBetween(min_value=200, max_value=20000),
        gxe.ExpectColumnValuesToNotBeNull(column="job_sk"),
        gxe.ExpectColumnValuesToBeUnique(column="job_sk"),
        gxe.ExpectColumnValuesToNotBeNull(column="job_id"),
        gxe.ExpectColumnValuesToBeUnique(column="job_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="company_sk"),
        gxe.ExpectColumnValuesToNotBeNull(column="location_sk"),
        gxe.ExpectColumnValuesToNotBeNull(column="posted_date_key"),
        gxe.ExpectColumnValuesToBeBetween(
            column="posted_date_key", min_value=20000101, max_value=20401231
        ),
        gxe.ExpectColumnValuesToNotBeNull(column="source"),
        gxe.ExpectColumnValuesToBeInSet(column="source", value_set=SOURCES),
        gxe.ExpectColumnValuesToNotBeNull(column="source_url"),
        gxe.ExpectColumnValuesToMatchRegex(column="source_url", regex="^https?://"),
        gxe.ExpectColumnValuesToBeBetween(column="salary_min", min_value=0, max_value=SALARY_MAX),
        gxe.ExpectColumnValuesToBeBetween(column="salary_max", min_value=0, max_value=SALARY_MAX),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
    ]


def dim_company_expectations():
    return [
        gxe.ExpectTableRowCountToBeBetween(min_value=50, max_value=20000),
        gxe.ExpectColumnValuesToNotBeNull(column="company_sk"),
        gxe.ExpectColumnValuesToBeUnique(column="company_sk"),
        gxe.ExpectColumnValuesToNotBeNull(column="company_name"),
        gxe.ExpectColumnValuesToBeUnique(column="company_name"),
        gxe.ExpectColumnValueLengthsToBeBetween(column="company_name", min_value=1),
    ]


SUITES = [
    ("jobs_staging", "staging_jobs", "jobs", "staging", staging_jobs_expectations),
    ("jobs_marts", "fact_jobs", "fact_jobs", "marts", fact_jobs_expectations),
    ("companies_marts", "dim_company", "dim_company", "marts", dim_company_expectations),
]


def main():
    if "--ephemeral" in sys.argv:
        context = gx.get_context(mode="ephemeral")
    else:
        context = gx.get_context(mode="file", project_root_dir=GX_ROOT)
    ds = add_or_get_datasource(context, "jobatlas_pg", pg_url())

    safe_delete(context.checkpoints, "jobatlas_dq")
    validations = []
    for suite_name, asset_name, table, schema, exp_fn in SUITES:
        safe_delete(context.validation_definitions, suite_name)
        safe_delete(context.suites, suite_name)

        asset = add_or_get_asset(ds, asset_name, table, schema)
        batch_def = add_or_get_batch_def(asset, "whole_table")

        suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
        for exp in exp_fn():
            suite.add_expectation(exp)
        suite.save()

        vd = context.validation_definitions.add(
            gx.ValidationDefinition(name=suite_name, data=batch_def, suite=suite)
        )
        validations.append(vd)

    checkpoint = context.checkpoints.add(
        gx.Checkpoint(
            name="jobatlas_dq",
            validation_definitions=validations,
            actions=[],
            result_format="SUMMARY",
        )
    )

    result = checkpoint.run()

    print("=" * 60)
    for ident, vr in result.run_results.items():
        print("PASS" if vr.success else "FAIL", "->", ident)
    print("=" * 60)
    print("OVERALL:", "PASS" if result.success else "FAIL")
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
