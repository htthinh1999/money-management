resource "google_secret_manager_secret" "google_credentials" {
  project   = var.project_id
  secret_id = "GOOGLE_CREDENTIALS"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "google_token" {
  project   = var.project_id
  secret_id = "GOOGLE_TOKEN"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}
