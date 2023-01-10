resource "kubernetes_namespace" "networking" {
  metadata {
    name = "networking"
  }

  lifecycle {
    ignore_changes = [metadata[0].labels]
  }
}

resource "kubernetes_secret" "ssl" {
  metadata {
    name      = "ssl"
    namespace = kubernetes_namespace.networking.metadata[0].name
  }

  type = "tls"

  data = {
    "tls.crt" = join("", [acme_certificate.certificate.certificate_pem, acme_certificate.certificate.issuer_pem])
    "tls.key" = acme_certificate.certificate.private_key_pem
  }
}
