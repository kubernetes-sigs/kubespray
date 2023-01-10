resource "kubernetes_secret" "argossl" {
  metadata {
    name      = "argocd-server-tls"
    namespace = "argocd"
  }

  type = "tls"

  data = kubernetes_secret.ssl.data
}

resource "kubernetes_manifest" "project" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "AppProject"
    metadata = {
      name      = "bootstrap"
      namespace = "argocd"
      labels = {
        "app.kubernetes.io/part-of" = "argocd"
      }
      finalizers = ["resources-finalizer.argocd.argoproj.io"]
    }
    spec = {
      sourceRepos = ["*"]

      destinations = [{
        namespace = "*"
        server    = "https://kubernetes.default.svc"
      }]

      syncWindows = [
        {
          kind         = "allow"
          schedule     = "10 */4 * * *"
          duration     = "1h"
          applications = ["*"]
          clusters     = ["*"]
          namespaces   = ["*"]
          timeZone     = "America/Toronto"
          manualSync   = true
        }
      ]

      clusterResourceWhitelist = [{
        group = "*"
        kind  = "*"
      }]

      namespaceResourceWhitelist = [{
        group = "*"
        kind  = "*"
      }]
    }
  }
  field_manager {
    force_conflicts = true
  }
}

resource "kubernetes_secret" "repository_credentials" {
  metadata {
    name      = "infra-repo-credentials"
    namespace = "argocd"
    labels = {
      "argocd.argoproj.io/secret-type" = "repo-creds"
    }
  }
  data = {
    type     = "git"
    url      = "https://git.yusufali.ca/infra"
    username = var.GIT_USERNAME
    password = var.GIT_PASSWORD
  }
}

resource "kubernetes_manifest" "application" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name       = kubernetes_manifest.project.manifest.metadata.name
      namespace  = "argocd"
      finalizers = ["resources-finalizer.argocd.argoproj.io"]
    }
    spec = {
      destination = {
        namespace = "argocd"
        server    = kubernetes_manifest.project.manifest.spec.destinations[0].server
      }

      project = kubernetes_manifest.project.manifest.metadata.name

      source = {
        path           = "charts/app"
        repoURL        = "https://github.com/drgroot/kubespray.git"
        targetRevision = "HEAD"

        helm = {
          values = <<-EOF
          spec:
            project: ${kubernetes_manifest.project.manifest.metadata.name}

          ingress:
            version: ${local.versions.ingress}
            namespace: ${kubernetes_namespace.networking.metadata[0].name}
            sslSecret: ${kubernetes_secret.ssl.metadata[0].namespace}/${kubernetes_secret.ssl.metadata[0].name}
            nodeIps: {${join(",",[for x in local.public_nodes: x.ip])}}

          keda:
            version: ${local.versions.keda}
          EOF
        }
      }

      syncPolicy = {
        automated = {
          prune    = true
          selfHeal = true
        }
      }
    }
  }

  field_manager {
    force_conflicts = true
  }
}
