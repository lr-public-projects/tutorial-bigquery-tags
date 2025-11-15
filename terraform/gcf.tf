locals {
  function_name                     = "bq-taxonomy"
  function_name_underscore          = replace(local.function_name, "-", "_")
  function_source_root_path         = "${path.root}/../function"
  function_source_code_path         = "${local.function_source_root_path}/${local.function_name_underscore}"
}
# Export Poetry dependencies
resource "null_resource" "poetry_export" {
  triggers = {
    poetry_lock_hash = filemd5("${local.function_source_root_path}/poetry.lock")
  }

  provisioner "local-exec" {
    command     = "poetry export -f requirements.txt --output ./${local.function_name_underscore}/requirements.txt --without-hashes"
    working_dir = local.function_source_root_path
  }
}

# Archive the function source code
data "archive_file" "archive" {
  type        = "zip"
  source_dir  = local.function_source_code_path
  output_path = "/tmp/${local.function_name}.zip"
  excludes = [
    "**/__pycache__/**"
  ]

  depends_on = [null_resource.poetry_export]
}

# Upload the archive to GCS
resource "google_storage_bucket_object" "source_archive" {
  name   = "${local.function_name}.${data.archive_file.archive.output_md5}.zip"
  bucket = var.terraform_bucket
  source = data.archive_file.archive.output_path
}

resource "google_cloudfunctions2_function" "cloud_function" {
    name = local.function_name
    project = var.project_id
    location = var.region
    description = "Cloud Function to sync Dataform taxonomy to BigQuery"
    build_config {
      runtime = "python312"
      entry_point = "bq_taxonomy"
      source {
        storage_source {
          bucket = var.terraform_bucket
          object = google_storage_bucket_object.source_archive.name
        }
      }
    }
    service_config {
      available_memory = "512Mi"
      timeout_seconds = 600
      ingress_settings = "ALLOW_ALL"
      max_instance_count = 1
      available_cpu = 0.1667
      min_instance_count = 0
      environment_variables = {
        PROJECT_ID = var.project_id
        REPOSITORY_ID = "data-governance"
        WORKSPACE_ID = "work"
        BASE_FOLDER = "definitions"
      }
    }
    labels = {
      "deployment-tool" = "terraform",
    }
}

resource "google_cloud_run_service_iam_binding" "cloud_function" {
  location = google_cloudfunctions2_function.cloud_function.location
  service  = google_cloudfunctions2_function.cloud_function.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}