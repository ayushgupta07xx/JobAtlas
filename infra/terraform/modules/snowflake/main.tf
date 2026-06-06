terraform {
  required_providers {
    snowflake = {
      source = "snowflakedb/snowflake"
    }
  }
}

# Compute warehouse for analytics / dbt transforms.
resource "snowflake_warehouse" "this" {
  name           = var.warehouse_name
  warehouse_size = var.warehouse_size
  auto_suspend   = var.auto_suspend_seconds
  comment        = "Analytics warehouse managed by Terraform"
}

# Logical database for marts.
resource "snowflake_database" "this" {
  name    = var.database_name
  comment = "Analytics database managed by Terraform"
}

# Marts schema inside the database.
resource "snowflake_schema" "marts" {
  database = snowflake_database.this.name
  name     = var.schema_name
  comment  = "dbt marts schema managed by Terraform"
}
