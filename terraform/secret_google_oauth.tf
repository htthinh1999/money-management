resource "google_secret_manager_secret" "google_oauth_state" {
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

resource "google_secret_manager_secret" "google_oauth_verifier" {
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

resource "google_secret_manager_secret" "google_oauth_redirect_uri" {
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
