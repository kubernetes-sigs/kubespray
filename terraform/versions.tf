locals {
  versions = {
    redis = "redis:6.2.5"
    minio = "minio/minio:RELEASE.2021-08-31T05-46-54Z"
    gitea = {
      name   = "gitea/gitea"
      semvar = "~1.x.x"
      tag    = "1.18"
    }
    drone = {
      name   = "drone/drone"
      tag    = "2.12.0"
      semvar = "~2"
    }
    verdaccio = {
      name   = "verdaccio/verdaccio"
      tag    = "5.15.4"
      semvar = "~5"
    }

    ingress    = "4.0.6"
    keda       = "2.8.1"
    nfs_provisioner = "4.0.17"
  }
}
