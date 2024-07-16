module "pubsub_money_management" {
  source     = "terraform-google-modules/pubsub/google"
  version    = "~> 6.0"
  topic      = "TOPIC_MONEY_MANAGEMENT"
  project_id = var.project_id
  push_subscriptions = [
    {
      name                         = "SUBSCRIPTION_PUSH_MONEY_MANAGEMENT"
      push_endpoint                = "${local.money_management_url}/webhook"
      max_delivery_attempts        = 5
      ack_deadline_seconds         = 20
      x-goog-version               = "v1beta1"
      expiration_policy            = ""
      maximum_backoff              = "600s"
      minimum_backoff              = "10s"
      enable_exactly_once_delivery = true
    }
  ]
}

resource "google_pubsub_topic_iam_member" "member" {
  project = var.project_id
  topic   = "TOPIC_MONEY_MANAGEMENT"
  role    = "roles/pubsub.publisher"
  member  = "allAuthenticatedUsers"
}
