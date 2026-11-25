terraform {
    required_version = ">= 1.5.0"

    required_providers {
        google = {
            source = "hashicorp/google"
            version = "~> 6.0"
        }
    }
}

provider "google" {
    project = var.project_id
    region = var.region
    zone = var.zone
}

resource "google_project_service" "required_apis" {
    for_each = toset([
        "compute.googleapis.com",
        "secretmanager.googleapis.com",
        "iap.googleapis.com"
    ])

    project = var.project_id
    service = each.key
    disable_on_destroy = false
}

resource "google_compute_network" "ai_tutor_vpc" {
    name = "ai-tutor-vpc"
    auto_create_subnetworks = false
    depends_on = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "ai_tutor_subnet" {
    name = "ai-tutor-subnet"
    ip_cidr_range = "10.10.0.0/24"
    region = var.region
    network = google_compute_network.ai_tutor_vpc.id
}

resource "google_compute_firewall" "allow_http_https" {
    name = "ai-tutor-allow-http-https"
    network = google_compute_network.ai_tutor_vpc.name

    allow {
        protocol = "tcp"
        ports = ["80", "443"]
    }

    source_ranges = ["0.0.0.0/0"]
    target_tags = ["ai-tutor-web"]
}

resource "google_compute_firewall" "allow_iap_ssh" {
    name = "ai-tutor-allow-iap-ssh"
    network = google_compute_network.ai_tutor_vpc.name

    allow {
        protocol = "tcp"
        ports = ["22"]
    }

    source_ranges = ["35.235.240.0/20"]
    target_tags = ["ai-tutor-web"]
}

resource "google_secret_manager_secret" "db_password" {
    secret_id = "ai-tutor-db-password"

    replication {
        auto{}
    }

    depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password_version" {
    secret = google_secret_manager_secret.db_password.id
    secret_data = var.db_password
}

resource "google_service_account" "vm_sa" {
    account_id = "ai-tutor-vm-sa"
    display_name = "AI TUTOR VM SERVICE ACCOUNT"
}

resource "google_secret_manager_secret_iam_member" "vm_secret_access" {
    secret_id = google_secret_manager_secret.db_password.id
    role = "roles/secretmanager.secretAccessor"
    member = "serviceAccount:${google_service_account.vm_sa.email}"
}

resource "google_compute_disk" "db_disk" {
    name = "ai-tutor-db-disk"
    type = "pd_balanced"
    zone = var.zone
    size = 20
}

resource "google_compute_disk" "models_disk" {
    name = "ai-tutor-models-disk"
    type = "pd_balanced"
    zone = var.zone
    size = 20
}

resource "google_compute_instance" "ai_tutor_vm" {
    name = "ai-tutor-vm"
    machine_type = var.machine_type
    zone = var.zone
    tags = ["ai-tutor-web"]

    boot_disk {
        initialize_params {
            image = "debian-cloud/debian-12"
            size = 30
            type = "pd_balanced"
        }
    }

    attached_disk {
        source = google_compute_disk.db_disk.id
        device_name = "db-disk"
    }

    attached_disk {
        source = google_compute_disk.models_disk.id
        device_name = "models-disk"
    }

    network_interface {
        subnetwork = google_compute_subnetwork.ai_tutor_subnet.id
        access_config {}
    } 
    
    service_account {
        email = google_service_account.vm_sa.email
        scopes = ["cloud-platform"]
    }

    metadata_startup_script = templatefile("${path.module}/start.sh", {
        repo_url = var.repo-url
        project_id = var.project_id
        db_secret_id = google_secret_manager_secret.db_password.secret_id
        db_name = var.db_name
        db_user = var.db_user
    })

    depends_on = [
        google_secret_manager_secret_version.db_password_version,
        google_secret_manager_secret_iam_member.vm_secret_access
    ]
}

