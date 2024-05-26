resource "google_secret_manager_secret" "mongo_host" {
  project   = var.project_id
  secret_id = "MONGO_DB_HOST"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "mongo_user" {
  project   = var.project_id
  secret_id = "MONGO_DB_USER"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "mongo_password" {
  project   = var.project_id
  secret_id = "MONGO_DB_PASSWORD"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

