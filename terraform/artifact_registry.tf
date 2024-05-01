resource "google_artifact_registry_repository" "repository" {
  project       = var.project_id
  location      = var.region
  repository_id = "repository"
  description   = "Docker repository"
  format        = "DOCKER"
}
