resource "google_bigquery_dataset" "tutorial_data" {
  dataset_id  = "TUTORIAL_DATA"
  friendly_name = "TUTORIAL_DATA"
  description = "Dataset para o tutorial de BigQuery Data Policies e Policy Tags"
  location    = "us"
}

resource "google_bigquery_table" "personal_info" {
  dataset_id          = google_bigquery_dataset.tutorial_data.dataset_id
  table_id            = "PERSONAL_INFO"
  deletion_protection = false

  schema = format("%s", jsonencode(
    [
      {
        "name" : "user_id",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "Identificador do usuário"
      },
      {
        "name" : "full_name",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "Nome completo do usuário"
      },
      {
        "name" : "email",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "E-mail do usuário",
        "policyTags" : {
          "names" : [
            google_data_catalog_policy_tag.pii_policy_email.name
          ]
        }
      },
      {
        "name" : "phone_number",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "Número de telefone do usuário",
      },
      {
        "name" : "physical_address",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "Endereço físico do usuário",
      },
      {
        "name" : "id_document",
        "type" : "STRING",
        "mode" : "NULLABLE",
        "description" : "Documento de identificação do usuário",
      }
    ]
  ))
}

resource "google_bigquery_table" "financial_info" {
  dataset_id          = google_bigquery_dataset.tutorial_data.dataset_id
  table_id            = "FINANCIAL_INFO"
  deletion_protection = false

  schema = jsonencode([
    {
      "name": "user_id",
      "type": "STRING",
      "mode": "NULLABLE",
      "description": "Identificador do usuário"
    },
    {
      "name": "pix_key",
      "type": "STRING",
      "mode": "NULLABLE",
      "description": "Chave PIX do usuário",
    },
    {
      "name": "bank_account",
      "type": "STRING",
      "mode": "NULLABLE",
      "description": "Número da conta bancária do usuário",
    },
    {
      "name": "credit_card_number",
      "type": "STRING",
      "mode": "NULLABLE",
      "description": "Número do cartão de crédito do usuário",
    }
  ])
}
