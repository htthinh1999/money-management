resource "google_cloud_scheduler_job" "scheduler_gmail_watch" {
  project          = var.project_id
  name             = "gmail-watch"
  description      = "This is a job to trigger Gmail watch API to watch for new emails"
  schedule         = "0 7 * * */1"
  time_zone        = "Asia/Vietnam"
  attempt_deadline = "320s"
  region           = "asia-southeast1"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "GET"
    uri         = "${local.money_management_url}/watch"
  }
}
