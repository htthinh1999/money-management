resource "google_secret_manager_secret" "google_credentials" {
  project   = var.project_id
  secret_id = "GOOGLE_OAUTH_STATE"
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
  secret_id = "GOOGLE_OAUTH_CODE_VERIFIER"
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
  secret_id = "GOOGLE_OAUTH_REDIRECT_URI"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}
