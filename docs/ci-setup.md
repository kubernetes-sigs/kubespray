# CI Setup

## Pipeline

1. unit-tests: fast jobs for fast feedback (linting, etc...)
2. deploy-part1: small number of jobs to test if the PR works with default settings
3. deploy-part2: slow jobs testing different platforms, OS, settings, CNI, etc...
4. deploy-part3: very slow jobs (upgrades, etc...)

## Runners

Kubespray has 3 types of GitLab runners:

- packet runners: used for E2E jobs (usually long)
- light runners: used for short lived jobs
- auto scaling runners: used for on-demand resources, see [GitLab docs](https://docs.gitlab.com/runner/configuration/autoscale.html) for more info

## Vagrant

Vagrant jobs are using the [quay.io/kubespray/vagrant](/test-infra/vagrant-docker/Dockerfile) docker image with `/var/run/libvirt/libvirt-sock` exposed from the host, allowing the container to boot VMs on the host.
