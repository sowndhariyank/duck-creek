variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "arsanjani-genai"
}

variable "region" {
  description = "The Google Cloud Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment Environment (staging, prod)"
  type        = string
  default     = "prod"
}

