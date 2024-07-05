terraform {
  required_version = ">= 1.3"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.36.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.36.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.1"
    }
  }
}
