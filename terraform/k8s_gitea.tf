resource "kubernetes_secret" "gitea" {
  metadata {
    name      = "gitea"
    namespace = "default"
  }

  data = {
    GITEA__database__DB_TYPE = "postgres"
    GITEA__database__HOST    = "${data.vault_generic_secret.postgres.data.hostname}:${data.vault_generic_secret.postgres.data.port}"
    GITEA__database__NAME    = "onedev"
    GITEA__database__USER    = "gitlab"
    GITEA__database__PASSWD  = data.vault_generic_secret.postgres.data.gitlab_password

    GITEA__service__DISABLE_REGISTRATION    = "true"
    GITEA__service__DEFAULT_USER_VISIBILITY = "limited"
    GITEA__service__DEFAULT_ORG_VISIBILITY  = "limited"

    GITEA__server__DOMAIN     = join(".",["git",data.cloudflare_zones.domain.zones[0].name])
    GITEA__server__ROOT_URL   = "https://${join(".",["git",data.cloudflare_zones.domain.zones[0].name])}"
    GITEA__server__SSH_DOMAIN = "bootstrap-tools-gitea.default.svc.cluster.local"

    GITEA__repository__DISABLED_REPO_UNITS = "repo.issues,repo.ext_issues,repo.wiki, repo.ext_wiki,repo.projects"
    GITEA__repository__DEFAULT_REPO_UNITS  = "repo.code,repo.releases,repo.pulls"
    GITEA__repository__DISABLE_STARS       = "true"
    GITEA__repository__DEFAULT_BRANCH      = "master"

    GITEA__ui__DEFAULT_THEME = "gitea"
  }
}
