resource "kubernetes_namespace" "nfs" {
  metadata {
    name = "nfs"
  }

  lifecycle {
    ignore_changes = [metadata[0].labels]
  }
}

data "vault_generic_secret" "rclone" {
  path = "external-infra/RCLONE"
}

resource "kubernetes_secret" "rclone_secret" {
  metadata {
    name      = "rclone"
    namespace = kubernetes_namespace.nfs.metadata[0].name
  }

  data = data.vault_generic_secret.rclone.data
}

resource "kubernetes_secret" "backup_script" {
  metadata {
    name      = "rclone-backup-scripts"
    namespace = kubernetes_namespace.nfs.metadata[0].name
  }

  data = {
    "upload.py"          = file("${path.module}/assets/scripts/upload.py")
    "googleSync.py"      = file("${path.module}/assets/scripts/googleSync.py")
    "backup_exclude.txt" = file("${path.module}/assets/configs/backup_exclude.txt")
  }
}

resource "kubernetes_manifest" "application_nfs" {
  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"
    metadata = {
      name       = "${kubernetes_manifest.project.manifest.metadata.name}-nfs"
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
        path           = "charts/nfs"
        repoURL        = "https://github.com/drgroot/kubespray.git"
        targetRevision = "HEAD"

        helm = {
          values = <<-EOF
          spec:
            project: ${kubernetes_manifest.project.manifest.metadata.name}

          storage:
            - name: onpremise
              hostname: ${var.STORAGE_HOSTNAME}
              mount_path: ${var.STORAGE_MOUNT}
              folders:
                - name: backups
                  backup: true
                - name: dynamic
                  backup: true
            - name: cloud
              hostname: ${local.storage_node.name}
              mount_path: /var/lib/mounts
              folders:
                - name: dynamic
                  backup: true
                - name: syncthing
                  syncthing: true
                  backup: true
                - name: media
                  google: true
                  fixed: true
                - name: downloads
                  fixed: true
          
          tasks:
            secrets:
              rclone: ${kubernetes_secret.rclone_secret.metadata[0].name}
              scripts: ${kubernetes_secret.backup_script.metadata[0].name}
            configs:
              - name: backup
                env:
                  - name: EXCLUDE_FILE
                    value: /scripts/backup_exclude.txt
                  - name: RCLONE_REMOTE
                    value: google_crypt:/backups
                  - name: BACKUP_PATH
                    value: /source
                args:
                  - /scripts/upload.py
              - name: google
                env:
                  - name: RCLONE_REMOTE
                    value: google:/data
                  - name: UPLOAD_MAX_AMOUNT
                    value: "750"
                  - name: BACKUP_PATH
                    value: /source
                args:
                  - /scripts/googleSync.py
              - name: syncthing
                env:
                  - name: EXCLUDE_FILE
                    value: /scripts/backup_exclude.txt
                  - name: RCLONE_REMOTE
                    value: /onpremise
                  - name: BACKUP_PATH
                    value: /source
                args:
                  - /scripts/upload.py
                volumeMounts:
                  - name: onpremise
                    mountPath: /onpremise
                    subPath: syncthing
                volumes:
                  - name: onpremise
                    nfs:
                      server: ${var.STORAGE_HOSTNAME}
                      path: ${var.STORAGE_MOUNT}

            versions:
              nfs_provisioner: ${local.versions.nfs_provisioner}
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
