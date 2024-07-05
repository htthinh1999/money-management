resource "google_storage_bucket" "money-management" {
  name          = "money-management"
  location      = "US-WEST1"
  force_destroy = true

  uniform_bucket_level_access = true

  #   cors {
  #     origin          = ["http://example.com"]
  #     method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
  #     response_header = ["*"]
  #     max_age_seconds = 3600
  #   }
}

resource "google_storage_bucket_iam_binding" "money-management" {
  bucket = google_storage_bucket.money-management.name
  role   = "roles/storage.objectViewer"

  members = [
    "allUsers",
  ]

  depends_on = [google_storage_bucket.money-management]
}

resource "google_storage_managed_folder" "user-token" {
  bucket = google_storage_bucket.money-management.name
  name   = "user-token/"

  depends_on = [google_storage_bucket.money-management]
}
