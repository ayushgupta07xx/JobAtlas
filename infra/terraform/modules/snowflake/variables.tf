variable "warehouse_name" {
  description = "Name of the virtual warehouse"
  type        = string
  default     = "JOBATLAS_TF_WH"
}

variable "warehouse_size" {
  description = "Warehouse size (XSMALL, SMALL, MEDIUM, ...)"
  type        = string
  default     = "XSMALL"
}

variable "auto_suspend_seconds" {
  description = "Seconds of inactivity before the warehouse auto-suspends"
  type        = number
  default     = 60
}

variable "database_name" {
  description = "Name of the analytics database"
  type        = string
  default     = "JOBATLAS_TF"
}

variable "schema_name" {
  description = "Name of the marts schema"
  type        = string
  default     = "MARTS"
}
