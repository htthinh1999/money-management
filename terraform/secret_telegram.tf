resource "google_secret_manager_secret" "telegram_money_bot_chat_id" {
  project   = var.project_id
  secret_id = "TELEGRAM_MONEY_BOT_CHAT_ID"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

resource "google_secret_manager_secret" "telegram_money_bot_token" {
  project   = var.project_id
  secret_id = "TELEGRAM_MONEY_BOT_TOKEN"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
}

