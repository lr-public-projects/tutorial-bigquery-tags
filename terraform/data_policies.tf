resource "google_data_catalog_taxonomy" "taxonomy" {
  region = "us"
  display_name = "Controle de Acesso"
  description = "Taxonomia para controlar o acesso a dados sensíveis"
  activated_policy_types = ["FINE_GRAINED_ACCESS_CONTROL"]
  depends_on = [ google_project_service.project_services ]
}

resource "google_data_catalog_policy_tag" "pii_policy" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  display_name = "PII"
  description  = "Tags para controle de acesso a dados PII"
}

resource "google_data_catalog_policy_tag" "pii_policy_email" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  parent_policy_tag = google_data_catalog_policy_tag.pii_policy.name
  display_name = "Email"
  description  = "Controle de acesso a e-mail"
}

resource "google_data_catalog_policy_tag" "pii_policy_phone" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  parent_policy_tag = google_data_catalog_policy_tag.pii_policy.name
  display_name = "Telefone"
  description  = "Controle de acesso a telefone"
}

resource "google_data_catalog_policy_tag" "pii_policy_address" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  parent_policy_tag = google_data_catalog_policy_tag.pii_policy.name
  display_name = "Endereço"
  description  = "Controle de acesso a endereços físicos"
}

resource "google_data_catalog_policy_tag" "pii_policy_document" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  parent_policy_tag = google_data_catalog_policy_tag.pii_policy.name
  display_name = "Documento"
  description  = "Controle de acesso a documentos de identificação (CPF, CNH, etc)"
}

resource "google_data_catalog_policy_tag" "financial_policy" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  display_name = "Dados financeiros"
  description  = "Tags para controle de acesso a dados financeiros"
}

resource "google_data_catalog_policy_tag" "financial_policy_pix" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  parent_policy_tag = google_data_catalog_policy_tag.financial_policy.name
  display_name = "Chave PIX"
  description  = "Controle de acesso a Chave Pix"
}

resource "google_data_catalog_policy_tag" "financial_policy_cc" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  parent_policy_tag = google_data_catalog_policy_tag.financial_policy.name
  display_name = "Conta Corrente ou Poupança"
  description  = "Controle de acesso a C/C ou C/P"
}

resource "google_data_catalog_policy_tag" "financial_policy_credit_card" {
  taxonomy = google_data_catalog_taxonomy.taxonomy.id
  parent_policy_tag = google_data_catalog_policy_tag.financial_policy.name
  display_name = "Cartão de Crédito ou Débito"
  description  = "Controle de acesso ao cartão de crédito/débito completo"
}

resource "google_bigquery_datapolicy_data_policy" "data_policy_email" {
  location = "us"
  data_policy_id = "data_policy_email"
  policy_tag = google_data_catalog_policy_tag.pii_policy_email.name
  data_policy_type = "DATA_MASKING_POLICY"  
  data_masking_policy {
    predefined_expression = "EMAIL_MASK"
  }
}

resource "google_bigquery_datapolicy_data_policy" "data_policy_phone" {
  location = "us"
  data_policy_id = "data_policy_phone"
  policy_tag = google_data_catalog_policy_tag.pii_policy_phone.name
  data_policy_type = "DATA_MASKING_POLICY"  
  data_masking_policy {
    predefined_expression = "LAST_FOUR_CHARACTERS"
  }
}

resource "google_bigquery_datapolicy_data_policy" "data_policy_pix" {
  location = "us"
  data_policy_id = "data_policy_pix"
  policy_tag = google_data_catalog_policy_tag.financial_policy_pix.name
  data_policy_type = "DATA_MASKING_POLICY"  
  data_masking_policy {
    predefined_expression = "ALWAYS_NULL"
  }
}