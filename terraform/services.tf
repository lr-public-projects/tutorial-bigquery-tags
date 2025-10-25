# PROJECT SERVICES
resource "google_project_service" "project_services" {
  project = var.project_id
  for_each = toset([
    "iam.googleapis.com",
    "serviceusage.googleapis.com",
    "datacatalog.googleapis.com",
    "bigquerydatapolicy.googleapis.com",
  ])
  service = each.key
  disable_on_destroy = false
  disable_dependent_services = true
  timeouts {
    create = "5m"
    update = "5m"
  }
}