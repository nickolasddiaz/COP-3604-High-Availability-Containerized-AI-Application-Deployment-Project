variable "project_id" {
    description = "GCP project IF"
    type = string
}

variable "region" {
    description = "GCP region"
    type = string
    default = "us-east1"
}

variable "zone" {
    description = "GCP zone"
    type = string
    default = "us-east1-b"
}

variable "machine_type" {
    description = "GCP vm size"
    type = string
    default = "e2-standard-4"
}

variable "repo_url" {
    description = "Github project link"
    type = string
    default = "https://github.com/nickolasddiaz/COP-3604-High-Availability-Containerized-AI-Application-Deployment-Project"
}

variable "db_user" {
    description = "database username"
    type = string
    default = "myuser"
}

variable "db_name" {
    description = "database name"
    type = string
    default = "mydatabase"
}

variable "db_password" {
    description = "database password saved"
    type = string
    sensitive = true
}