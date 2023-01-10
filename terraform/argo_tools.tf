resource "kubernetes_manifest" "application_tools" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name       = "${kubernetes_manifest.project.manifest.metadata.name}-tools"
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
        path           = "charts/tools"
        repoURL        = "https://github.com/drgroot/kubespray.git"
        targetRevision = "HEAD"

        helm = {
          values = <<-EOF
          spec:
            project: ${kubernetes_manifest.project.manifest.metadata.name}

          tools:
            - name: drone
              image:
                name: ${local.versions.drone.name}
                semvar: ${local.versions.drone.semvar}
                tag: ${local.versions.drone.tag}
              url: ${join(".",["drone",data.cloudflare_zones.domain.zones[0].name])}
              secrets: 
                - ${kubernetes_secret.drone.metadata[0].name}
              resources:
                requests:
                  cpu: 500m
                  memory: 512Mi
              ports:
                - port: 80
            - name: drone-runner
              namespace: ${kubernetes_namespace.drone_runner.metadata[0].name}
              serviceAccount: ${kubernetes_service_account_v1.drone_runner.metadata[0].name}
              image:
                name: "drone/drone-runner-kube"
                tag: "latest"
                semvar: "latest"
              ports:
                - port: 3000
              resources:
                requests:
                  cpu: 250m
                  memory: 512Mi
              secrets:
                - drone-runner
            - name: gitea
              image:
                name: ${local.versions.gitea.name}
                semvar: ${local.versions.gitea.semvar}
                tag: ${local.versions.gitea.tag}
                suffix: "-rootless"
              url: ${join(".",["git",data.cloudflare_zones.domain.zones[0].name])}
              secrets:
                - ${kubernetes_secret.gitea.metadata[0].name}
              ports:
                - port: 3000
                - port: 2222
              securityContext:
                runAsGroup: 1000
                runAsUser: 1000
              resources:
                requests:
                  cpu: 2
                  memory: 4Gi
              className: nfs-cloud-syncthing
              volumes:
                - mountPath: /var/lib/gitea
                  subPath: data
                - mountPath: /etc/gitea
                  subPath: config
            - name: registry
              image:
                name: registry
                semvar: ~2
                tag: 2
              url: ${join(".",["registry",data.cloudflare_zones.domain.zones[0].name])}
              secrets:
                - ${kubernetes_secret.registry.metadata[0].name}
              ports:
                - port: 5000
              className: nfs-onpremise-dynamic
              ingress:
                annotations:
                  nginx.ingress.kubernetes.io/client-body-buffer-size: 5000m
                  nginx.ingress.kubernetes.io/proxy-body-size: 5000m
                  nginx.ingress.kubernetes.io/ssl-redirect: "true"
              securityContext:
                runAsGroup: 1000
                runAsUser: 1000
              resources:
                requests:
                  cpu: 500m
                  memory: 1Gi
              volumes:
                - mountPath: /var/lib/registry
              extraVolumes:
                - name: htpasswd
                  secret:
                    secretName: ${kubernetes_secret.registryAuth.metadata[0].name}
              extraVolumeMounts:
                - name: htpasswd
                  mountPath: /auth
            - name: verdaccio
              image:
                name: ${local.versions.verdaccio.name}
                semvar: ${local.versions.verdaccio.semvar}
                tag: ${local.versions.verdaccio.tag}
              url: ${join(".",["npm",data.cloudflare_zones.domain.zones[0].name])}
              secrets:
                - ${kubernetes_secret.verdaccio.metadata[0].name}
              ports:
                - port: 4873
              className: nfs-onpremise-dynamic
              ingress:
                annotations:
                  nginx.ingress.kubernetes.io/client-body-buffer-size: 500m
                  nginx.ingress.kubernetes.io/proxy-body-size: 500m
                  nginx.ingress.kubernetes.io/ssl-redirect: "true"
              securityContext:
                runAsGroup: 1000
                runAsUser: 1000
              env:
                - name: VERDACCIO_PORT
                  value: '4873'
              resources:
                requests:
                  cpu: 250m
                  memory: 512Mi
              volumes:
                - mountPath: /verdaccio/storage/data
              extraVolumes:
                - name: htpasswd
                  secret:
                    secretName: ${kubernetes_secret.verdaccio.metadata[0].name}
              extraVolumeMounts:
                - name: htpasswd
                  mountPath: /verdaccio/conf
                  readOnly: true
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
