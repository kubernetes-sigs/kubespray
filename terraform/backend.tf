terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "3.6.0"
    }

    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "3.4.0"
    }

    acme = {
      source  = "vancluever/acme"
      version = "2.12.0"
    }

    htpasswd = {
      source  = "loafoe/htpasswd"
      version = "1.0.1"
    }

    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.16.1"
    }

    tls = {
      source  = "hashicorp/tls"
      version = "3.1.0"
    }

    helm = {
      source  = "hashicorp/helm"
      version = "2.3.0"
    }

     minio = {
      source = "aminueza/minio"
      version = "1.10.0"
    }
  }

  required_version = ">=1"
}

provider "kubernetes" {
  config_path = var.ADMIN_CONF
}

provider "helm" {
  kubernetes {
    config_path = var.ADMIN_CONF
  }
}

provider "vault" {
  skip_child_token = true
  address = var.VAULT_ADDRESS
  auth_login {
    path = "auth/userpass/login/${var.VAULT_USERNAME}"

    parameters = {
      password = var.VAULT_PASSWORD
    }
  }
}

provider "cloudflare" {
  api_key = var.CLOUDFLARE_API_KEY
  email = var.CLOUDFLARE_EMAIL
}

provider "htpasswd" {
  # Configuration options
}

provider "acme" {
  server_url = "https://acme-v02.api.letsencrypt.org/directory"
}