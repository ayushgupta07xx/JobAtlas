terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.17"
    }
  }
}

# All credentials are read from environment variables; `terraform validate`
# requires none of them. Before `terraform apply`, export:
#   SNOWFLAKE_ORGANIZATION_NAME, SNOWFLAKE_ACCOUNT_NAME,
#   SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_ROLE
provider "snowflake" {}

module "snowflake" {
  source         = "../../modules/snowflake"
  warehouse_name = var.warehouse_name
  database_name  = var.database_name
  schema_name    = var.schema_name
}
