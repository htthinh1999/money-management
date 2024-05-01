terraform {
  backend "gcs" {
    bucket = "keycode-mon-tf-state"
    prefix = "terraform/state"
  }
}
