resource "kubernetes_secret" "verdaccio" {
  metadata {
    name      = "verdaccio-registry-auth"
    namespace = "default"
  }

  data = {
    htpasswd = "${random_password.registryusername.result}:${htpasswd_password.hash.bcrypt}"

    "config.yaml" = <<-EOF
    storage: /verdaccio/storage/data
    auth:
      htpasswd:
        file: /verdaccio/conf/htpasswd
        max_users: -1
        algorithm: bcrypt
        rounds: 10

    uplinks:
      npmjs:
        url: https://registry.npmjs.org/
        cache: false
        agent_options:
          keepAlive: true
          maxSockets: 40
          maxFreeSockets: 10

    packages:
      '@*/*':
        access: $all
        publish: $authenticated
        proxy: NONE

      '**':
        access: $all
        proxy: NONE

    middlewares:
      audit:
        enabled: true

    logs: {type: stdout, format: pretty, level: http}
    EOF
  }
}
