data "cloudflare_zones" "domain" {
  filter {
    name = var.DOMAIN_NAME
  }
}

data "vault_generic_secret" "secrets" {
  path = "kubernetes/TENANTS" 
}

locals {
  namespace_cnames = flatten([
    for x in jsondecode(data.vault_generic_secret.secrets.data.tenants) : concat([
      contains(x.flags, "dns") ? ["*.${x.namespace}", x.namespace] : [],
    ])
  ])
  all_cnames = concat(
      [
        "*",
        data.cloudflare_zones.domain.zones[0].name,
      ],
      local.namespace_cnames
    )
}

resource "cloudflare_record" "kubemain" {
  zone_id = data.cloudflare_zones.domain.zones[0].id
  name    = "kube"
  value   = local.public_nodes[0].ip
  type    = "A"
  ttl     = 1
  proxied = false
}

resource "cloudflare_record" "roundrobin" {
  count = length(local.public_nodes)

  zone_id = data.cloudflare_zones.domain.zones[0].id
  name    = "server"
  value   = local.public_nodes[count.index].ip
  type    = "A"
  ttl     = 1
  proxied = false
}

resource "cloudflare_record" "mail" {
  for_each = {
    "aspmx.l.google.com" : "1",
    "alt1.aspmx.l.google.com" : "5",
    "alt2.aspmx.l.google.com" : "5",
    "alt3.aspmx.l.google.com" : "10",
    "alt4.aspmx.l.google.com" : "10",
  }

  zone_id  = data.cloudflare_zones.domain.zones[0].id
  name     = "@"
  value    = each.key
  type     = "MX"
  priority = each.value
}

resource "cloudflare_record" "subdomains" {
  count = length(local.all_cnames)

  zone_id = data.cloudflare_zones.domain.zones[0].id
  name    = local.all_cnames[count.index]
  value   = "server.${data.cloudflare_zones.domain.zones[0].name}"
  type    = "CNAME"
  proxied = false
  ttl     = 1
}

# SSL Key generation
resource "tls_private_key" "tls_private" {
  algorithm = "RSA"
}

resource "random_password" "certificate_password" {
  length  = 16
  special = false
}

resource "acme_registration" "reg" {
  account_key_pem = tls_private_key.tls_private.private_key_pem
  email_address   = "ali@yusuf.email"
}

resource "acme_certificate" "certificate" {
  account_key_pem = acme_registration.reg.account_key_pem
  common_name     = data.cloudflare_zones.domain.zones[0].name
  subject_alternative_names = concat(
    ["*.${data.cloudflare_zones.domain.zones[0].name}"],
    [
      for x in local.namespace_cnames : "${x}.${data.cloudflare_zones.domain.zones[0].name}" if length(split(".", x)) > 1
    ],
  )
  certificate_p12_password = random_password.certificate_password.result

  dns_challenge {
    provider = "cloudflare"

    config = {
      CLOUDFLARE_EMAIL = var.CLOUDFLARE_EMAIL
      CLOUDFLARE_API_KEY = var.CLOUDFLARE_API_KEY
    }
  }
}
