#!/bin/sh

docker run -d --name gitlab-runner --restart always -v /srv/gitlab-runner/cache:/srv/gitlab-runner/cache -v /srv/gitlab-runner/config:/etc/gitlab-runner -v /var/run/docker.sock:/var/run/docker.sock gitlab/gitlab-runner:v1.10.0

#
#/srv/gitlab-runner/config# cat config.toml
#concurrent = 10
#check_interval = 1

#[[runners]]
#  name = "2edf3d71fe19"
#  url = "https://gitlab.com"
#  token = "THE TOKEN-CHANGEME"
#  executor = "docker"
#  [runners.docker]
#    tls_verify = false
#    image = "docker:latest"
#    privileged = true
#    disable_cache = false
#    cache_dir = "/srv/gitlab-runner/cache"
#    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/srv/gitlab-runner/cache:/cache:rw"]
#  [runners.cache]
