data "google_iam_policy" "fine_grained_readers" {
  binding {
    role = "roles/datacatalog.categoryFineGrainedReader"
    members = var.unmasked_pii_readers
  }
}

resource "google_data_catalog_policy_tag_iam_policy" "unmasked_pii_reader_binding" {
  policy_tag = google_data_catalog_policy_tag.pii_policy.name
  policy_data = data.google_iam_policy.fine_grained_readers.policy_data

  depends_on = [ google_data_catalog_policy_tag.pii_policy ]
}

resource "google_data_catalog_policy_tag_iam_policy" "unmasked_financial_reader_binding" {
  policy_tag = google_data_catalog_policy_tag.financial_policy.name
  policy_data = data.google_iam_policy.fine_grained_readers.policy_data

  depends_on = [ google_data_catalog_policy_tag.financial_policy ]
}

resource "google_bigquery_datapolicy_data_policy_iam_binding" "masked_readers" {
  project = var.project_id
  location       = "us"
  data_policy_id = google_bigquery_datapolicy_data_policy.data_policy_email.data_policy_id
  role           = "roles/bigquerydatapolicy.maskedReader"
  members        = var.masked_pii_readers
}

resource "google_project_iam_binding" "job_users" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  members = distinct(concat(var.unmasked_pii_readers, var.masked_pii_readers))
}

resource "google_project_iam_binding" "data_viewers" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  members = distinct(concat(var.unmasked_pii_readers, var.masked_pii_readers))
}