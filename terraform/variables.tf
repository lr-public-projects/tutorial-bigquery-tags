variable "project_id" {
  description = "ID do projeto no GCP"
  type        = string
}

variable "region" {
  description = "Região do GCP"
  type        = string
  default     = "us-central1"
}

variable "unmasked_pii_readers" {
  description = "Leitores de dados abertos"
  type = list(string)
}

variable "masked_pii_readers" {
  description = "Leitores de dados protegidos"
  type = list(string)
}