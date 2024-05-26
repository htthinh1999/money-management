data "google_secret_manager_secret_version" "telegram_money_bot_token" {
  project = var.project_id
  secret  = "TELEGRAM_MONEY_BOT_TOKEN"
  version = "latest"
}

data "google_secret_manager_secret_version" "telegram_money_bot_chat_id" {
  project = var.project_id
  secret  = "TELEGRAM_MONEY_BOT_CHAT_ID"
  version = "latest"
}

data "google_secret_manager_secret_version" "mongo_db_host" {
  project = var.project_id
  secret  = "MONGO_DB_HOST"
  version = "latest"
}

data "google_secret_manager_secret_version" "mongo_db_user" {
  project = var.project_id
  secret  = "MONGO_DB_USER"
  version = "latest"
}

data "google_secret_manager_secret_version" "mongo_db_password" {
  project = var.project_id
  secret  = "MONGO_DB_PASSWORD"
  version = "latest"
}

resource "google_cloud_run_v2_service" "money_management_service" {
  name         = "money-management"
  project      = var.project_id
  location     = var.region
  ingress      = "INGRESS_TRAFFIC_ALL"
  launch_stage = "GA"

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  template {
    max_instance_request_concurrency = 5
    execution_environment            = "EXECUTION_ENVIRONMENT_GEN2"

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    containers {
      image = "asia-southeast1-docker.pkg.dev/keycode-mon/repository/money-management:0.0.4"
      name  = "money-management"
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          memory = "512Mi"
          cpu    = 1
        }
      }

      env {
        name  = "BROWSER"
        value = "chrome"
      }

      env {
        name  = "GOOGLE_CREDENTIALS_FILE"
        value = "credentials.json"
      }

      env {
        name  = "GOOGLE_TOKEN_FILE"
        value = "token.json"
      }

      env {
        name  = "GOOGLE_PUBSUB_TOPIC"
        value = "projects/keycode-mon/topics/TOPIC_MONEY_MANAGEMENT"
      }

      env {
        name = "TELEGRAM_BOT_TOKEN"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret_version.telegram_money_bot_token.secret
            version = "latest"
          }
        }
      }

      env {
        name = "TELEGRAM_CHAT_ID"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret_version.telegram_money_bot_chat_id.secret
            version = "latest"
          }
        }
      }

      env {
        name = "MONGO_DB_HOST"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret_version.mongo_db_host.secret
            version = "latest"
          }
        }
      }

      env {
        name = "MONGO_DB_USER"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret_version.mongo_db_user.secret
            version = "latest"
          }
        }
      }

      env {
        name = "MONGO_DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret_version.mongo_db_password.secret
            version = "latest"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      client,
      client_version,
      labels,
      template[0].labels,
      template[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_v2_service_iam_member" "money_management_run_all_users" {
  project    = var.project_id
  location   = var.region
  name       = "money-management"
  role       = "roles/run.invoker"
  member     = "allUsers"
  depends_on = [google_cloud_run_v2_service.money_management_service]
}


locals {
  money_management_url = google_cloud_run_v2_service.money_management_service.uri
}
