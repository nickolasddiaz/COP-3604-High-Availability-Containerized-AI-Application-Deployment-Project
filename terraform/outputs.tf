output "vm_public_ip" {
    description = "AI Tutor VM Public IP Address"
    value = google_compute_instance.ai_tutor_vm.network_interface[0].access_config[0].nat_ip
}

output "iap_ssh_command" {
    description = "Google Cloud Proxy SSH Command"
    value = "gcloud compute ssh ${google_compute_instance.ai_tutor_vm.name} --zone=${var.zone} --project=${var.project_id} --tunnel-through-iap"
}