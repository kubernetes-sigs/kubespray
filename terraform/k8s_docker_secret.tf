data "vault_generic_secret" "docker" {
  path = "external-infra/DOCKER"
}

resource "random_password" "registryusername" {
  length  = 30
  special = false
  upper   = false
}

resource "random_password" "registrypassword" {
  length  = 30
  special = false
  upper   = false
}

resource "htpasswd_password" "hash" {
  password = random_password.registrypassword.result
  salt     = substr(sha512(random_password.registrypassword.result), 0, 8)
}

resource "kubernetes_secret" "registryAuth" {
  metadata {
    name      = "docker-registry-auth"
    namespace = "default"
  }

  data = {
    htpasswd = "${random_password.registryusername.result}:${htpasswd_password.hash.bcrypt}"
  }
}

resource "kubernetes_secret" "registry" {
  metadata {
    name      = "docker-registry-secret"
    namespace = "default"
  }

  data = {
    REGISTRY_AUTH                = "htpasswd"
    REGISTRY_AUTH_HTPASSWD_PATH  = "/auth/htpasswd"
    REGISTRY_AUTH_HTPASSWD_REALM = "Local Registry Realm"
    REGISTRY_STORAGE_MAINTENANCE = <<EOF
      uploadpurging:
        enabled: true
        age: 48h
        interval: 24h
        dryrun: false
      readonly:
        enabled: false
      delete:
        enabled: true
    EOF
  }
}

resource "kubernetes_secret" "docker_credentials" {
  for_each = merge(
    {
      (kubernetes_namespace.drone_runner.metadata[0].name) = kubernetes_namespace.drone_runner.metadata[0].name
      default                                              = "default"
      argocd                                               = "argocd"
      (kubernetes_namespace.nfs.metadata[0].name)          = kubernetes_namespace.nfs.metadata[0].name
    }
  )

  metadata {
    name      = "cluster-docker-secret"
    namespace = each.key
  }

  data = {
    ".dockerconfigjson" = jsonencode({
      auths = {
        "${join(".",["registry",data.cloudflare_zones.domain.zones[0].name])}" = {
          auth = "${base64encode("${random_password.registryusername.result}:${random_password.registrypassword.result}")}"
        },
        "https://index.docker.io/v1/" : {
          "auth" : "${base64encode("${data.vault_generic_secret.docker.data.username}:${data.vault_generic_secret.docker.data.password}")}"
        }
      }
    })
  }

  type = "kubernetes.io/dockerconfigjson"
}

resource "kubernetes_default_service_account_v1" "default_sa" {
  for_each = merge(
    {
      (kubernetes_namespace.drone_runner.metadata[0].name) = kubernetes_namespace.drone_runner.metadata[0].name
      default                                              = "default"
      (kubernetes_namespace.nfs.metadata[0].name)          = kubernetes_namespace.nfs.metadata[0].name
    }
  )

  metadata {
    namespace = each.key
  }

  image_pull_secret {
    name = kubernetes_secret.docker_credentials[each.key].metadata[0].name
  }

  lifecycle {
    ignore_changes = [secret]
  }
}
