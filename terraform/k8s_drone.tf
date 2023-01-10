data "vault_generic_secret" "drone" {
  path = "external-infra/DRONE"
}

data "vault_generic_secret" "postgres" {
  path = "external-infra/DATABASE_POSTGRES"
}

resource "kubernetes_secret" "drone" {
  metadata {
    name      = "drone-secret"
    namespace = "default"
  }

  data = {
    DRONE_GITEA_SERVER        = "https://${join(".",["git",data.cloudflare_zones.domain.zones[0].name])}"
    DRONE_GITEA_CLIENT_ID     = data.vault_generic_secret.drone.data.DRONE_GITEA_CLIENT_ID
    DRONE_GITEA_CLIENT_SECRET = data.vault_generic_secret.drone.data.DRONE_GITEA_CLIENT_SECRET
    DRONE_GITEA_SKIP_VERIFY   = "true"

    DRONE_GIT_ALWAYS_AUTH = "true"

    DRONE_SERVER_HOST         = join(".",["drone",data.cloudflare_zones.domain.zones[0].name])
    DRONE_SERVER_PROTO        = "https"
    DRONE_DATABASE_DRIVER     = "postgres"
    DRONE_DATABASE_DATASOURCE = "postgres://gitlab:${data.vault_generic_secret.postgres.data.gitlab_password}@${data.vault_generic_secret.postgres.data.hostname}:${data.vault_generic_secret.postgres.data.port}/drone?sslmode=disable"
    DRONE_REGISTRATION_CLOSED = "false"

    DRONE_RPC_SECRET = data.vault_generic_secret.drone.data.DRONE_RPC_SECRET
  }
}

resource "kubernetes_namespace" "drone_runner" {
  metadata {
    name = "drone-runner"
  }

  lifecycle {
    ignore_changes = [metadata[0].labels]
  }
}

resource "kubernetes_service_account_v1" "drone_runner" {
  metadata {
    name      = kubernetes_namespace.drone_runner.metadata[0].name
    namespace = kubernetes_namespace.drone_runner.metadata[0].name
  }

  image_pull_secret {
    name = kubernetes_secret.docker_credentials["default"].metadata[0].name
  }
}

resource "kubernetes_role" "drone_runner" {
  metadata {
    name      = kubernetes_service_account_v1.drone_runner.metadata[0].name
    namespace = kubernetes_service_account_v1.drone_runner.metadata[0].namespace
  }

  rule {
    api_groups = [""]
    resources  = ["secrets"]
    verbs      = ["create", "delete"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods", "pods/log"]
    verbs      = ["get", "create", "delete", "list", "watch", "update"]
  }
}

resource "kubernetes_role_binding" "drone_runner" {
  metadata {
    name      = "binding"
    namespace = kubernetes_namespace.drone_runner.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account_v1.drone_runner.metadata[0].name
    namespace = kubernetes_namespace.drone_runner.metadata[0].name
  }

  role_ref {
    kind      = "Role"
    name      = kubernetes_role.drone_runner.metadata[0].name
    api_group = "rbac.authorization.k8s.io"
  }
}

resource "kubernetes_secret" "drone_runner" {
  metadata {
    name      = kubernetes_namespace.drone_runner.metadata[0].name
    namespace = kubernetes_namespace.drone_runner.metadata[0].name
  }

  data = {
    DRONE_RPC_HOST          = "${kubernetes_manifest.application_tools.manifest.metadata.name}-drone.default.svc.cluster.local:80"
    DRONE_NAMESPACE_DEFAULT = kubernetes_namespace.drone_runner.metadata[0].name
    DRONE_RPC_PROTO         = "http"
    DRONE_RPC_SECRET        = kubernetes_secret.drone.data.DRONE_RPC_SECRET
  }
}
