resource "kubernetes_manifest" "appsproject" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "AppProject"
    metadata = {
      name      = "apps"
      namespace = "argocd"
      labels = {
        "app.kubernetes.io/part-of" = "argocd"
      }
      finalizers = ["resources-finalizer.argocd.argoproj.io"]
    }
    spec = {
      sourceRepos = ["*"]
      destinations = [{
        namespace = "argocd"
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
      clusterResourceBlacklist = [{
        group = "*"
        kind  = "*"
      }]
      namespaceResourceWhitelist = [{
        group = "*"
        kind  = "Application"
      }]
    }
  }
  field_manager {
    force_conflicts = true
  }
}
